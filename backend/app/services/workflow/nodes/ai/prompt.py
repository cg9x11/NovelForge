
from app.locales import schema_field_description
from typing import Any, Dict, Optional, Union, AsyncIterator
from pydantic import BaseModel, Field
from loguru import logger
from ...registry import register_node
from ..base import BaseNode
from app.services.prompt_service import get_prompt, get_prompt_by_identifier, render_prompt


class PromptLoadInput(BaseModel):
    prompt_id: Union[int, str] = Field(
        ...,
        description=schema_field_description("prompt_id"),
        json_schema_extra={"x-component": "PromptSelect"}
    )
    variables: Optional[Dict[str, Any]] = Field(None, description=schema_field_description("variables"))


class PromptLoadOutput(BaseModel):
    text: str = Field(..., description=schema_field_description("text"))


@register_node
class PromptLoadNode(BaseNode[PromptLoadInput, PromptLoadOutput]):


    node_type = "Prompt.Load"
    category = "data"
    label = "Load Prompt"
    description = "Load a prompt template"

    input_model = PromptLoadInput
    output_model = PromptLoadOutput

    async def execute(self, inputs: PromptLoadInput) -> AsyncIterator[PromptLoadOutput]:
        variables = inputs.variables or {}

        try:
            prompt_obj = None

            if isinstance(inputs.prompt_id, int):
                prompt_obj = get_prompt(self.context.session, inputs.prompt_id)
            else:
                prompt_obj = get_prompt_by_identifier(self.context.session, str(inputs.prompt_id))

            if not prompt_obj:
                raise ValueError(f"\u672a\u627e\u5230\u63d0\u793a\u8bcd: {inputs.prompt_id}")

            template_vars = {
                **self.context.variables,
                **variables,
            }

            rendered_text = render_prompt(prompt_obj.template, template_vars)

            logger.info(
                f"[Prompt.Load] \u52a0\u8f7d\u63d0\u793a\u8bcd\u6210\u529f: prompt={inputs.prompt_id}, "
                f"length={len(rendered_text)}"
            )

            yield PromptLoadOutput(text=rendered_text)

        except Exception as e:
            raise
