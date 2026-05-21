
from app.locales import schema_field_description
import json
from typing import Any, Dict, Optional, AsyncIterator
from pydantic import BaseModel, Field
from loguru import logger

from ...registry import register_node
from ..base import BaseNode
from app.services.ai.core.chat_model_factory import build_chat_model
from langchain_core.messages import HumanMessage, SystemMessage


# ============================================================
# Input/Output Models
# ============================================================

class LLMInput(BaseModel):
    user_prompt: str = Field(..., description=schema_field_description("user_prompt"))
    system_prompt: Optional[str] = Field(None, description=schema_field_description("system_prompt"))
    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"), gt=0)
    temperature: float = Field(0.7, description=schema_field_description("temperature"), ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description=schema_field_description("max_tokens"), gt=0)
    timeout: int = Field(60, description=schema_field_description("timeout"), gt=0)
    max_retry: int = Field(3, description=schema_field_description("max_retry"), ge=0, le=10)


class LLMOutput(BaseModel):
    response: str = Field(..., description=schema_field_description("response"))
    usage: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("usage"))


def _extract_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, list):
        parts = [_extract_text(item) for item in value]
        return "".join([part for part in parts if part])

    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            return text

        content = value.get("content")
        if content is not None:
            extracted = _extract_text(content)
            if extracted:
                return extracted

        for key in ("output_text", "message", "reasoning_content", "value"):
            field_val = value.get(key)
            if field_val is None:
                continue
            extracted = _extract_text(field_val)
            if extracted:
                return extracted

        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)

    if hasattr(value, "model_dump"):
        try:
            dumped = value.model_dump()
            return _extract_text(dumped)
        except Exception:
            pass

    if hasattr(value, "content"):
        try:
            return _extract_text(getattr(value, "content"))
        except Exception:
            pass

    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


# ============================================================
# Node Implementation
# ============================================================

@register_node
class LLMGenerateNode(BaseNode[LLMInput, LLMOutput]):


    node_type = "AI.LLM"
    category = "ai"
    label = "LLM Call"
    description = "Call a large language model to generate text"

    input_model = LLMInput
    output_model = LLMOutput

    async def execute(self, input_data: LLMInput) -> AsyncIterator[LLMOutput]:

        try:
            model = build_chat_model(
                session=self.context.session,
                llm_config_id=input_data.llm_config_id,
                temperature=input_data.temperature,
                max_tokens=input_data.max_tokens,
                timeout=input_data.timeout,
            )
        except Exception as e:
            raise ValueError(f"\u6784\u5efa\u6a21\u578b\u5931\u8d25: {str(e)}")

        messages = []
        if input_data.system_prompt:
            messages.append(SystemMessage(content=input_data.system_prompt))
        messages.append(HumanMessage(content=input_data.user_prompt))

        last_error = None
        for attempt in range(input_data.max_retry + 1):
            try:
                response = await model.ainvoke(messages)

                payload = response.content if hasattr(response, 'content') else response
                response_text = _extract_text(payload)

                usage = {}
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                elif hasattr(response, 'response_metadata'):
                    meta = response.response_metadata
                    if isinstance(meta, dict):
                        usage = meta.get('usage', {})

                logger.info(
                    f"[AI.LLM] LLM \u8c03\u7528\u6210\u529f (\u5c1d\u8bd5 {attempt + 1}/{input_data.max_retry + 1}): "
                    f"llm_config_id={input_data.llm_config_id}, response_length={len(response_text)}"
                )

                yield LLMOutput(
                    response=response_text,
                    usage=usage
                )
                return

            except Exception as e:
                last_error = e
                if attempt < input_data.max_retry:
                    logger.warning(
                        f"[AI.LLM] LLM \u8c03\u7528\u5931\u8d25 (\u5c1d\u8bd5 {attempt + 1}/{input_data.max_retry + 1}), "
                        f"\u5c06\u91cd\u8bd5: {str(e)}"
                    )
                else:
                    logger.error(
                        f"[AI.LLM] LLM \u8c03\u7528\u5931\u8d25,\u5df2\u8fbe\u6700\u5927\u91cd\u8bd5\u6b21\u6570 ({input_data.max_retry + 1}): {str(e)}"
                    )

        raise RuntimeError(f"LLM \u8c03\u7528\u5931\u8d25 (\u91cd\u8bd5{input_data.max_retry}\u6b21\u540e): {str(last_error)}")

