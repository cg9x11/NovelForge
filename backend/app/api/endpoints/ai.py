from app.locales import localized_text
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.ai import ContinuationRequest, ContinuationResponse, GeneralAIRequest
from app.schemas.response import ApiResponse
from app.services import prompt_service, llm_config_service

from app.services.schema_service import compose_full_schema
from app.utils.stream_utils import wrap_sse_stream
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import Type, Dict, Any, List
import json

from app.db.models import Card, CardType
from app.utils.schema_utils import filter_schema_for_ai

from app.services.knowledge_service import KnowledgeService
from app.schemas.entity import DYNAMIC_INFO_TYPES
from app.schemas import entity as entity_schemas
from app.core import emit_event
from app.services.ai.core import llm_service
from app.services.ai.core.model_builder import build_model_from_json_schema
from app.services.ai.generation.continuation_context_service import enrich_continuation_context_info
from app.services.ai.generation.continuation_budget_runtime import estimate_required_call_count
from app.services.ai.generation.instruction_validator import validate_instruction, apply_instruction
from app.services.ai.generation.instruction_generator import generate_instruction_stream
from app.services.ai.generation.prompt_builder import build_instruction_system_prompt
from app.schemas.instruction import InstructionGenerateRequest
from app.schemas.wizard import Tags as _Tags
from loguru import logger

router = APIRouter()

from app.schemas.response_registry import RESPONSE_MODEL_MAP


@router.get("/schemas", response_model=Dict[str, Any], summary=localized_text('hardcoded.api_endpoints_ai_2a784a20'))
def get_all_schemas(session: Session = Depends(get_session)):
    """Endpoint documentation."""
    all_definitions: Dict[str, Any] = {}

    for name, model_class in RESPONSE_MODEL_MAP.items():
        schema = model_class.model_json_schema(ref_template="#/$defs/{model}")
        if '$defs' in schema:
            all_definitions.update(schema['$defs'])
            del schema['$defs']
        all_definitions[name] = schema

    try:
        cc = all_definitions.get('CharacterCard')
        if isinstance(cc, dict):
            props = (cc.get('properties') or {})
            if 'dynamic_info' in props:
                item_schema = {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "info": {"type": "string"},
                        "weight": {"type": "number"}
                    },
                    "required": ["id", "info", "weight"]
                }
                enum_values = DYNAMIC_INFO_TYPES
                props['dynamic_info'] = {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        ev: {"type": "array", "items": item_schema} for ev in enum_values
                    },
                    "description": localized_text('hardcoded.api_endpoints_ai_4b7004d0')
                }
                cc['properties'] = props
                all_definitions['CharacterCard'] = cc
    except Exception:
        pass

    try:
        entity_models = [
            entity_schemas.DynamicInfoItem,
            entity_schemas.DynamicInfo,
            entity_schemas.UpdateDynamicInfo,
        ]
        for mdl in entity_models:
            sch = mdl.model_json_schema(ref_template="#/$defs/{model}")
            if '$defs' in sch:
                all_definitions.update(sch['$defs'])
                del sch['$defs']
            all_definitions[mdl.__name__] = sch
    except Exception:
        pass

    return all_definitions

@router.get("/content-models", response_model=List[str], summary=localized_text('hardcoded.api_endpoints_ai_7f37948d'))
def get_content_models(session: Session = Depends(get_session)):
    return list(RESPONSE_MODEL_MAP.keys())


@router.get("/config-options", summary=localized_text('hardcoded.api_endpoints_ai_470f5d62'))
async def get_ai_config_options(session: Session = Depends(get_session)):
    """Endpoint documentation."""
    try:
        llm_configs = llm_config_service.get_llm_configs(session)
        prompts = prompt_service.get_prompts(session)
        response_models = get_content_models(session)
        return ApiResponse(data={
            "llm_configs": [{"id": config.id, "display_name": config.display_name or config.model_name} for config in llm_configs],
            "prompts": [{"id": prompt.id, "key": getattr(prompt, "key", None), "name": prompt.name, "description": prompt.description, "built_in": getattr(prompt, 'built_in', False)} for prompt in prompts],
            "available_tasks": [],
            "response_models": response_models
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config options: {str(e)}")

@router.get("/prompts/render", summary=localized_text('hardcoded.api_endpoints_ai_94189388'))
async def render_prompt_with_knowledge(name: str, session: Session = Depends(get_session)):
    p = prompt_service.get_prompt_by_identifier(session, name)
    if not p or not p.template:
        raise HTTPException(status_code=404, detail={"error_code": "PROMPT_NOT_FOUND", "prompt_name": name})
    try:
        text = prompt_service.inject_knowledge(session, str(p.template))
        return ApiResponse(data={"text": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")

@router.post("/generate", summary=localized_text('hardcoded.api_endpoints_ai_a8fa3406'))
async def generate_ai_content(
    request: GeneralAIRequest = Body(...),
    session: Session = Depends(get_session),
):
    """Generate AI content with a caller-provided response_model_schema."""
    if not request.input or not request.llm_config_id or not request.prompt_name:
        raise HTTPException(status_code=400, detail="Missing required generation parameters: input, llm_config_id, or prompt_name")
    if request.response_model_schema is None:
        raise HTTPException(status_code=400, detail="Please provide response_model_schema")

    try:
        composed = compose_full_schema(session, request.response_model_schema)
        schema_for_prompt = filter_schema_for_ai(composed) if request.exclude_ai_fields else composed
        resp_model = build_model_from_json_schema('DynamicResponseModel', schema_for_prompt or composed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create dynamic model: {e}")

    prompt = prompt_service.get_prompt_by_identifier(session, request.prompt_name)
    if not prompt:
        raise HTTPException(status_code=400, detail={"error_code": "PROMPT_NAME_NOT_FOUND", "prompt_name": request.prompt_name})

    prompt_template = prompt_service.inject_knowledge(session, prompt.template or '')

    schema_json = json.dumps(schema_for_prompt if schema_for_prompt is not None else resp_model.model_json_schema(), indent=2, ensure_ascii=False)
    system_prompt = (
        f"{prompt_template}\n\n"
        f"```json\n{schema_json}\n```"
    )

    user_prompt = request.input['input_text']
    deps_str = request.deps or ""

    try:
        result = await llm_service.generate_structured(
            session=session,
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            output_type=resp_model,
            llm_config_id=request.llm_config_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout=request.timeout,
            deps=deps_str,
        )
    except ValueError as e:
        logger.exception(
            "[AI Generate] structured generation failed "
            f"llm_config_id={request.llm_config_id} "
            f"prompt_name={request.prompt_name} "
            f"response_model={getattr(resp_model, '__name__', str(resp_model))} "
            f"error={type(e).__name__}: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(
            "[AI Generate] unexpected structured generation error "
            f"llm_config_id={request.llm_config_id} "
            f"prompt_name={request.prompt_name} "
            f"response_model={getattr(resp_model, '__name__', str(resp_model))} "
            f"error={type(e).__name__}: {e}"
        )
        raise HTTPException(status_code=500, detail=f"Generation failed: {type(e).__name__}: {e}")
    card: Card | None = None
    try:
        card_id = None
        if isinstance(request.input, dict):
            card_id = request.input.get('card_id')
        if card_id:
            card = session.get(Card, int(card_id))
        project_id = None
        if isinstance(request.input, dict):
            project_id = request.input.get('project_id') or (card.project_id if card else None)
        emit_event("generate.finished", {
            "session": session,
            "card": card,
            "project_id": int(project_id) if project_id else (card.project_id if card else None)
        })
    except Exception:
        pass
    return ApiResponse(data=result)

@router.post("/generate/continuation",
             response_model=ApiResponse[ContinuationResponse],
             summary=localized_text('hardcoded.api_endpoints_ai_75102855'),
             responses={
                 200: {
                     "content": {
                         "application/json": {},
                         "text/event-stream": {}
                     },
                     "description": localized_text('hardcoded.api_endpoints_ai_dd9c8026')
                 }
             })
async def generate_continuation(
    request: ContinuationRequest,
    session: Session = Depends(get_session),
):
    try:
        if not request.prompt_name:
            raise HTTPException(status_code=400, detail="Continuation requires prompt_name")
        p = prompt_service.get_prompt_by_identifier(session, request.prompt_name)
        if not p or not p.template:
            raise HTTPException(status_code=400, detail={"error_code": "PROMPT_NAME_NOT_FOUND", "prompt_name": request.prompt_name})
        system_prompt = prompt_service.inject_knowledge(session, str(p.template))


        request.context_info = enrich_continuation_context_info(session, request)


        if request.stream:
            expected_calls = estimate_required_call_count(request)
            ok, reason = llm_config_service.can_consume(session, request.llm_config_id, 0, 0, expected_calls)
            if not ok:
                raise HTTPException(status_code=400, detail=f"Insufficient LLM quota: {reason}")
            async def _stream_and_trigger():
                content_acc = []
                async for chunk in llm_service.generate_continuation_streaming(session, request, system_prompt):
                    content_acc.append(chunk)
                    yield chunk
                try:
                    emit_event("generate.finished", {
                        "session": session,
                        "card": None,
                        "project_id": request.project_id
                    })
                except Exception:
                    pass
            return StreamingResponse(wrap_sse_stream(_stream_and_trigger()), media_type="text/event-stream")
        else:
            content_parts = []
            async for chunk in llm_service.generate_continuation_streaming(session, request, system_prompt):
                content_parts.append(chunk)
            result = "".join(content_parts)
            try:
                emit_event("generate.finished", {
                    "session": session,
                    "card": None,
                    "project_id": request.project_id
                })
            except Exception:
                pass
            return ApiResponse(data=ContinuationResponse(content=result))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/models/tags", response_model=_Tags, summary=localized_text('hardcoded.api_endpoints_ai_5384bfe6'))
def export_tags_model():
    return _Tags()




@router.post("/generate/stream", summary=localized_text('hardcoded.api_endpoints_ai_2cf7eecc'))
async def generate_with_instruction_stream(
    request: InstructionGenerateRequest,
    session: Session = Depends(get_session),
):
    """Stream generated instructions for frontend execution and repair."""
    async def event_generator():
        try:
            full_schema = compose_full_schema(session, request.response_model_schema)

            card_prompt_content = None
            if request.prompt_template:
                from app.services import prompt_service
                from loguru import logger
                prompt = prompt_service.get_prompt_by_identifier(session, request.prompt_template)
                if prompt and prompt.template:
                    card_prompt_content = prompt_service.inject_knowledge(session, str(prompt.template))
                    logger.info(f"[CardGeneration] Loaded prompt template: {request.prompt_template}, length: {len(card_prompt_content)}")
                else:
                    logger.warning(f"[CardGeneration] Prompt template not found: {request.prompt_template}")

            system_prompt = build_instruction_system_prompt(
                session=session,
                schema=full_schema,
                card_prompt=card_prompt_content
            )

            llm_config = llm_config_service.get_llm_config(session, request.llm_config_id)
            logger.info(
                "[CardGeneration] Starting instruction stream "
                f"llm_config_id={request.llm_config_id} "
                f"provider={getattr(llm_config, 'provider', None)} "
                f"model={getattr(llm_config, 'model_name', None)} "
                f"api_protocol={getattr(llm_config, 'api_protocol', None)} "
                f"prompt_template={request.prompt_template}"
            )

            async for event in generate_instruction_stream(
                session=session,
                llm_config_id=request.llm_config_id,
                user_prompt=request.user_prompt,
                system_prompt=system_prompt,
                schema=full_schema,
                current_data=request.current_data,
                conversation_context=request.conversation_context,
                context_info=request.context_info,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                timeout=request.timeout or 150
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Instruction flow generation failed: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "error_code": "GENERATION_FAILED",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
