from app.locales import schema_field_description
from typing import Any, AsyncIterator, Dict

from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import LLMConfig
from ...registry import register_node
from ..base import BaseNode


class SelectLLMInput(BaseModel):


    llm_config_id: int | None = Field(
        default=None,
        description=schema_field_description("llm_config_id"),
        json_schema_extra={"x-component": "LLMSelect"},
    )
    llm_name: str | None = Field(
        default=None,
        description=schema_field_description("llm_name"),
        json_schema_extra={"x-component": "LLMSelect"},
    )


class SelectLLMOutput(BaseModel):


    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"))
    llm_config: Dict[str, Any] = Field(..., description=schema_field_description("llm_config"))


@register_node
class SelectLLMNode(BaseNode[SelectLLMInput, SelectLLMOutput]):
    node_type = "Logic.SelectLLM"
    category = "logic"
    label = "Select LLM"
    description = "Select an LLM configuration"

    input_model = SelectLLMInput
    output_model = SelectLLMOutput

    async def execute(self, inputs: SelectLLMInput) -> AsyncIterator[SelectLLMOutput]:
        session = self.context.session

        config = None
        if inputs.llm_config_id is not None:
            config = session.get(LLMConfig, inputs.llm_config_id)

        if config is None and inputs.llm_name:
            exact_stmt = select(LLMConfig).where(
                (LLMConfig.display_name == inputs.llm_name)
                | (LLMConfig.model_name == inputs.llm_name)
            )
            exact = session.exec(exact_stmt).all()
            if len(exact) == 1:
                config = exact[0]
            elif len(exact) > 1:
                raise ValueError(f"\u6a21\u578b\u540d\u5339\u914d\u5230\u591a\u4e2a\u5019\u9009: {inputs.llm_name}")
            else:
                all_rows = session.exec(select(LLMConfig)).all()
                lowered = inputs.llm_name.lower()
                matches = [
                    item
                    for item in all_rows
                    if lowered in (item.display_name or "").lower()
                    or lowered in (item.model_name or "").lower()
                ]
                if len(matches) == 1:
                    config = matches[0]
                elif len(matches) > 1:
                    raise ValueError(f"\u6a21\u578b\u540d\u5339\u914d\u5230\u591a\u4e2a\u5019\u9009: {inputs.llm_name}")

        if not config:
            raise ValueError(
                f"LLM \u914d\u7f6e\u4e0d\u5b58\u5728: id={inputs.llm_config_id}, name={inputs.llm_name}"
            )

        logger.info(
            f"[SelectLLM] \u9009\u62e9\u6a21\u578b: {config.display_name or config.model_name} "
            f"(id={config.id})"
        )

        yield SelectLLMOutput(
            llm_config_id=config.id,
            llm_config={
                "id": config.id,
                "display_name": config.display_name,
                "model_name": config.model_name,
                "provider": config.provider,
                "api_base": config.api_base,
            },
        )
