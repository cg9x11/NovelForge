from app.locales import schema_field_description
from typing import Any, Dict, AsyncIterator
from pydantic import Field, BaseModel
from loguru import logger

from ...registry import register_node
from ..base import BaseNode
from ...expressions import evaluate_expression


class LogicAssertInput(BaseModel):
    condition: str = Field(..., description=schema_field_description("condition"))
    message: str = Field("Assertion failed", description=schema_field_description("message"))


class LogicAssertOutput(BaseModel):
    pass


@register_node
class LogicAssertNode(BaseNode[LogicAssertInput, LogicAssertOutput]):
    node_type = "Logic.Assert"
    category = "logic"
    label = "Assert"
    description = "Validate condition and stop workflow on failure"

    input_model = LogicAssertInput
    output_model = LogicAssertOutput

    async def execute(self, inputs: LogicAssertInput) -> AsyncIterator[LogicAssertOutput]:
        try:
            eval_context = {
                **self.context.variables
            }

            result = evaluate_expression(inputs.condition, eval_context)
            is_true = bool(result)

            if not is_true:
                raise AssertionError(f"\u65ad\u8a00\u5931\u8d25: {inputs.message}")

            yield LogicAssertOutput()

        except Exception as e:
            if isinstance(e, AssertionError):
                raise
            raise ValueError(f"\u65ad\u8a00\u6761\u4ef6\u6c42\u503c\u5931\u8d25: {str(e)}")
