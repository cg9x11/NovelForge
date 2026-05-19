"""ç»“æž„åŒ–ç”ŸæˆèŠ‚ç‚¹

åˆ©ç”¨æŒ‡ä»¤æµç”ŸæˆæœåŠ¡ï¼ˆInstruction Generatorï¼‰å®žçŽ°ç»“æž„åŒ–æ•°æ®çš„ç”Ÿæˆã€‚
æ”¯æŒè‡ªåŠ¨æ ¡éªŒã€è‡ªåŠ¨ä¿®å¤å’Œ Pydantic æ¨¡åž‹è¾“å‡ºã€‚
"""

from typing import Any, Dict, Optional, List, AsyncIterator, TYPE_CHECKING
from pydantic import BaseModel, Field
from loguru import logger

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from ...registry import register_node
from ..base import BaseNode
from app.services import prompt_service
from app.services.ai.core.model_builder import build_model_from_json_schema
from app.services.ai.core.llm_service import generate_structured
from app.services.schema_service import compose_full_schema
from app.db.models import CardType
from app.schemas.response_registry import RESPONSE_MODEL_MAP
from sqlmodel import select


class StructuredGenerateInput(BaseModel):
    """ç»“æž„åŒ–ç”Ÿæˆè¾“å…¥"""
    user_prompt: str = Field(..., description="ç”¨æˆ·æç¤ºè¯")
    llm_config_id: int = Field(..., description="LLMé…ç½®ID", json_schema_extra={"x-component": "LLMSelect"})
    response_model_id: str = Field(..., description="å“åº”æ¨¡åž‹", json_schema_extra={"x-component": "ResponseModelSelect"})
    context: Optional[Dict[str, Any]] = Field(None, description="ä¸Šä¸‹æ–‡æ•°æ®/åˆå§‹æ•°æ®")
    schema_extra: Optional[Dict[str, Any]] = Field(None, description="é¢å¤–çš„ Schema å®šä¹‰ (å¯é€‰)")
    max_retry: int = Field(3, description="æœ€å¤§é‡è¯•/ä¿®å¤æ¬¡æ•°")
    prompt_template: Optional[str] = Field(None, description="æç¤ºè¯æ¨¡ç‰ˆåç§°(å¯é€‰)", json_schema_extra={"x-component": "PromptSelect"})
    temperature: float = Field(0.7, description="æ¸©åº¦å‚æ•°")
    max_tokens: Optional[int] = Field(None, description="æœ€å¤§tokenæ•°")
    timeout: int = Field(60, description="è¶…æ—¶æ—¶é—´(ç§’)")
    fail_soft: bool = Field(False, description="å¤±è´¥æ—¶æ˜¯å¦é™çº§è¿”å›žç©ºç»“æžœè€ŒéžæŠ›é”™")
    use_instruction_flow: bool = Field(
        False,
        description="æ˜¯å¦ä½¿ç”¨æŒ‡ä»¤æµæ¨¡å¼ï¼ˆå¤æ‚ç»“æž„æŽ¨èå¼€å¯ï¼Œç®€å•ç»“æž„å¯å…³é—­ä»¥ä½¿ç”¨åŽŸç”Ÿç»“æž„åŒ–ï¼‰",
    )


class StructuredGenerateOutput(BaseModel):
    """ç»“æž„åŒ–ç”Ÿæˆè¾“å‡º"""
    data: Dict[str, Any] = Field(..., description="ç”Ÿæˆçš„ç»“æž„åŒ–æ•°æ®")
    logs: List[Dict[str, Any]] = Field(..., description="ç”Ÿæˆè¿‡ç¨‹æ—¥å¿—")

@register_node
class StructuredGenerateNode(BaseNode[StructuredGenerateInput, StructuredGenerateOutput]):
    """ç»“æž„åŒ–ç”ŸæˆèŠ‚ç‚¹"""
    
    node_type = "AI.StructuredGenerate"
    category = "ai"
    label = "ç»“æž„åŒ–ç”Ÿæˆ"
    description = "ç”Ÿæˆç¬¦åˆæŒ‡å®š Schema çš„ç»“æž„åŒ–æ•°æ® (æ”¯æŒè‡ªåŠ¨ä¿®å¤)"
    
    input_model = StructuredGenerateInput
    output_model = StructuredGenerateOutput

    @classmethod
    def get_output_schema_contract(
        cls,
        config: Dict[str, Any],
        session=None,
    ) -> Optional[Dict[str, Any]]:
        """å£°æ˜Žè¾“å‡º `data` å­—æ®µçš„ schema å¥‘çº¦ã€‚

        å¥‘çº¦æ ¼å¼ï¼š
        {
            "kind": "structured_output",
            "schema_id": "è§’è‰²å¡",
            "data_path": "data"
        }
        """
        model_id = config.get("response_model_id")
        if not isinstance(model_id, str) or not model_id.strip():
            return None

        return {
            "kind": "structured_output",
            "schema_id": model_id.strip(),
            "data_path": "data",
        }

    async def execute(
        self,
        inputs: StructuredGenerateInput
    ) -> AsyncIterator[StructuredGenerateOutput]:
        """æ‰§è¡Œç”Ÿæˆ"""
        session = self.context.session
        user_prompt = inputs.user_prompt
        current_data = inputs.context or {}
        
        # 1. èŽ·å–ç›®æ ‡ Schema
        target_schema = self._get_schema(session, inputs)
        if not target_schema:
            raise ValueError(f"æ— æ³•åŠ è½½æ¨¡åž‹ Schema: {inputs.response_model_id}")
            
        # 2. å‡†å¤‡å‚æ•°
        # ç»„è£…å®Œæ•´ Schema (å¤„ç† $ref)
        full_schema = compose_full_schema(session, target_schema)

        # åŠ è½½æç¤ºè¯æ¨¡æ¿ï¼ˆå¦‚æžœé…ç½®äº†ï¼‰
        card_prompt_content = None
        if inputs.prompt_template:
            prompt = prompt_service.get_prompt_by_identifier(session, inputs.prompt_template)
            if prompt and prompt.template:
                card_prompt_content = prompt.template
        
        logger.info(f"[AI.Structured] å¼€å§‹ç”Ÿæˆ: model={inputs.response_model_id}")

        # 3. è°ƒç”¨æŒ‡ä»¤æµèšåˆç”Ÿæˆï¼ˆèŠ‚ç‚¹å±‚ä¿æŒéžæµå¼ï¼‰
        try:
            dynamic_output = build_model_from_json_schema(
                f"WorkflowStructured_{inputs.response_model_id}",
                full_schema,
            )
            generated = await generate_structured(
                session=session,
                llm_config_id=inputs.llm_config_id,
                user_prompt=user_prompt,
                output_type=dynamic_output,
                system_prompt=card_prompt_content,
                deps="",
                temperature=inputs.temperature,
                max_tokens=inputs.max_tokens,
                timeout=inputs.timeout,
                max_retries=inputs.max_retry,
                use_instruction_flow=inputs.use_instruction_flow,
                track_stats=True,
                return_logs=True,
            )
        except Exception as e:
            if inputs.fail_soft:
                logger.warning(
                    f"[AI.Structured] ç”Ÿæˆå¤±è´¥ä½†å¯ç”¨ fail_softï¼Œè¿”å›žé™çº§ç»“æžœ: model={inputs.response_model_id}, err={e}"
                )
                yield StructuredGenerateOutput(data=current_data or {}, logs=[{"type": "error", "text": str(e)}])
                return
            logger.exception(f"[AI.Structured] æ‰§è¡Œå¼‚å¸¸")
            raise

        result_data = generated["result"].model_dump(mode="json")

        yield StructuredGenerateOutput(
            data=result_data,
            logs=generated["logs"],
        )

    def _get_schema(self, session, inputs: StructuredGenerateInput) -> Optional[Dict[str, Any]]:
        """æ ¹æ®é…ç½®èŽ·å– JSON Schema
        """
        
        stmt = select(CardType).where(CardType.name == inputs.response_model_id)
        ct = session.exec(stmt).first()
        if ct and ct.json_schema:
            return ct.json_schema

        builtin_model = RESPONSE_MODEL_MAP.get(inputs.response_model_id)
        if builtin_model is not None:
            return builtin_model.model_json_schema(ref_template="#/$defs/{model}")
                
        return None

