
from app.locales import schema_field_description
import copy
import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING, Union

from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from app.db.models import CardType
from app.services.card_type_service_utils import get_card_type_by_identifier
from app.schemas.response_registry import RESPONSE_MODEL_MAP
from app.services.ai.core.model_builder import build_model_from_json_schema
from app.services.ai.core.llm_service import generate_structured
from ...expressions.evaluator import evaluate_expression
from ...registry import register_node
from ..base import BaseNode


class SequentialStructuredInput(BaseModel):


    items: List[Any] = Field(..., description=schema_field_description("items"))
    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"), json_schema_extra={"x-component": "LLMSelect"})
    prompt_template: str = Field(
        ...,
        description=schema_field_description("prompt_template"),
        json_schema_extra={"x-component": "Textarea"},
    )
    response_model_id: str = Field(..., description=schema_field_description("response_model_id"), json_schema_extra={"x-component": "ResponseModelSelect"})
    temperature: Optional[float] = Field(
        None,
        description=schema_field_description("temperature"),
        ge=0.0,
        le=2.0,
    )
    max_tokens: Optional[int] = Field(
        None,
        description=schema_field_description("max_tokens"),
        ge=1,
    )
    timeout: Optional[float] = Field(
        None,
        description=schema_field_description("timeout"),
        gt=0,
    )
    max_retries: int = Field(3, description=schema_field_description("max_retries"), ge=1)
    use_instruction_flow: bool = Field(
        False,
        description=schema_field_description("use_instruction_flow"),
    )
    overlap_size: int = Field(0, description=schema_field_description("overlap_size"), ge=0)
    initial_carry: Optional[Dict[str, Any]] = Field(None, description=schema_field_description("initial_carry"))
    carry_extract_expr: Optional[str] = Field(
        None,
        description=schema_field_description("carry_extract_expr"),
        json_schema_extra={"x-component": "Textarea"},
    )
    fail_soft: bool = Field(False, description=schema_field_description("fail_soft"))


class SequentialStructuredOutput(BaseModel):


    results: List[Dict[str, Any]] = Field(..., description=schema_field_description("results"))
    final_carry: Dict[str, Any] = Field(..., description=schema_field_description("final_carry"))
    errors: List[Dict[str, Any]] = Field(..., description=schema_field_description("errors"))


@register_node
class SequentialStructuredNode(BaseNode[SequentialStructuredInput, SequentialStructuredOutput]):


    node_type = "AI.SequentialStructured"
    category = "ai"
    label = "Sequential Structured Generation"
    description = "Generate structured data for items sequentially"

    input_model = SequentialStructuredInput
    output_model = SequentialStructuredOutput

    async def execute(
        self,
        inputs: SequentialStructuredInput,
    ) -> AsyncIterator[Union["ProgressEvent", SequentialStructuredOutput]]:
        from ...engine.async_executor import ProgressEvent

        items = inputs.items
        if not isinstance(items, list):
            raise ValueError("Invalid sequential structured input")

        if not inputs.prompt_template:
            raise ValueError("Invalid sequential structured input")

        if not items:
            yield SequentialStructuredOutput(
                results=[],
                final_carry=copy.deepcopy(inputs.initial_carry or {}),
                errors=[],
            )
            return

        total = len(items)
        schema = self._get_schema(self.context.session, inputs)
        if not schema:
            raise ValueError(f"\u65e0\u6cd5\u52a0\u8f7d\u6a21\u578b Schema: {inputs.response_model_id}")
        dynamic_output = build_model_from_json_schema(
            f"SequentialStructured_{inputs.response_model_id}",
            schema,
        )

        checkpoint = getattr(self.context, "checkpoint", None) or {}
        results = self._normalize_result_list(checkpoint.get("partial_results", []))
        errors = self._normalize_result_list(checkpoint.get("errors", []))
        processed_indices = self._normalize_index_set(checkpoint.get("processed_indices", []), total)

        carry_state = checkpoint.get("carry_state")
        if not isinstance(carry_state, dict):
            carry_state = copy.deepcopy(inputs.initial_carry or {})

        current_index = checkpoint.get("current_index")
        if not isinstance(current_index, int):
            current_index = len(results)

        current_index = max(current_index, len(results), len(processed_indices))
        current_index = min(current_index, total)

        if current_index > 0:
            logger.info(
                f"[SequentialStructured] \u4ece\u68c0\u67e5\u70b9\u6062\u590d: \u5df2\u5904\u7406 {current_index}/{total}, "
                f"errors={len(errors)}"
            )

        if current_index >= total:
            yield SequentialStructuredOutput(
                results=results,
                final_carry=carry_state,
                errors=errors,
            )
            return

        for index in range(current_index, total):
            item = items[index]
            carry_in = copy.deepcopy(carry_state)

            try:
                rendered_prompt = self._render_prompt(
                    template=inputs.prompt_template,
                    item=item,
                    carry=carry_in,
                    overlap_size=inputs.overlap_size,
                )

                generated = await generate_structured(
                    session=self.context.session,
                    llm_config_id=inputs.llm_config_id,
                    user_prompt=rendered_prompt,
                    output_type=dynamic_output,
                    system_prompt=None,
                    deps="",
                    temperature=inputs.temperature or 0.7,
                    max_tokens=inputs.max_tokens,
                    timeout=inputs.timeout or 150,
                    max_retries=inputs.max_retries,
                    use_instruction_flow=inputs.use_instruction_flow,
                    track_stats=True,
                    return_logs=True,
                )
                ai_result = generated["result"].model_dump(mode="json")

                carry_out = self._extract_carry(
                    expr=inputs.carry_extract_expr,
                    ai_result=ai_result,
                    item=item,
                    carry=carry_in,
                    index=index,
                    results=results,
                    errors=errors,
                )

                result_item = {
                    "index": index,
                    "ai_result": ai_result,
                    "logs": generated["logs"],
                    "meta": item,
                    "carry_in": carry_in,
                    "carry_out": carry_out,
                }
                results.append(result_item)
                carry_state = carry_out
                processed_indices.add(index)

            except Exception as e:
                error_item = {"index": index, "item": item, "error": str(e)}
                errors.append(error_item)

                if not inputs.fail_soft:
                    raise

                results.append(
                    {
                        "index": index,
                        "error": str(e),
                        "meta": item,
                        "carry_in": carry_in,
                        "carry_out": carry_state,
                    }
                )
                processed_indices.add(index)

            percent = ((index + 1) / total) * 100
            yield ProgressEvent(
                percent=percent,
                message=f"\u5df2\u5904\u7406 {index + 1}/{total} \u4e2a\u9879\u76ee",
                data={
                    "current_index": index + 1,
                    "processed_indices": sorted(processed_indices),
                    "carry_state": carry_state,
                    "partial_results": results,
                    "errors": errors,
                },
            )

        yield SequentialStructuredOutput(
            results=results,
            final_carry=carry_state,
            errors=errors,
        )

    def _render_prompt(
        self,
        template: str,
        item: Any,
        carry: Dict[str, Any],
        overlap_size: int,
    ) -> str:
        content = self._extract_content(item)
        rendered = template.replace("{{content}}", str(content))
        rendered = rendered.replace("{{item}}", self._to_text(item))
        rendered = rendered.replace("{{carry}}", self._to_text(carry))
        rendered = rendered.replace("{{overlap_size}}", str(overlap_size))

        rendered = self._render_prefix_fields(rendered, "item", item)
        rendered = self._render_prefix_fields(rendered, "carry", carry)
        return rendered

    def _render_prefix_fields(self, text: str, prefix: str, value: Any, path: Optional[List[str]] = None) -> str:
        current_path = path or []
        placeholder = "{{" + ".".join([prefix, *current_path]) + "}}"

        if current_path:
            text = text.replace(placeholder, self._to_text(value))

        if isinstance(value, dict):
            for key, child in value.items():
                text = self._render_prefix_fields(text, prefix, child, [*current_path, str(key)])

        return text

    def _extract_content(self, item: Any) -> str:
        if not isinstance(item, dict):
            return str(item)

        content = ""
        path = item.get("path")

        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
            except Exception as e:
                content = f"[\u8bfb\u53d6\u5931\u8d25: {e}]"

        if not content and "content" in item:
            content = self._to_text(item.get("content"))

        return content

    def _extract_carry(
        self,
        expr: Optional[str],
        ai_result: Any,
        item: Any,
        carry: Dict[str, Any],
        index: int,
        results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not expr:
            return copy.deepcopy(carry)

        next_carry = evaluate_expression(
            expr,
            {
                "ai_result": ai_result,
                "item": item,
                "carry": carry,
                "index": index,
                "results": results,
                "errors": errors,
            },
        )

        if next_carry is None:
            return {}

        if not isinstance(next_carry, dict):
            raise ValueError("Invalid sequential structured input")

        return next_carry

    def _normalize_result_list(self, value: Any) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    def _normalize_index_set(self, value: Any, total: int) -> set[int]:
        if not isinstance(value, list):
            return set()

        normalized: set[int] = set()
        for item in value:
            try:
                index = int(item)
            except Exception:
                continue

            if 0 <= index < total:
                normalized.add(index)

        return normalized

    def _to_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)

        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)

    def _get_schema(self, session, inputs: SequentialStructuredInput) -> Optional[Dict[str, Any]]:


        ct = get_card_type_by_identifier(session, inputs.response_model_id)
        if ct and ct.json_schema:
            return ct.json_schema

        builtin_model = RESPONSE_MODEL_MAP.get(inputs.response_model_id)
        if builtin_model is not None:
            return builtin_model.model_json_schema(ref_template="#/$defs/{model}")

        return None
