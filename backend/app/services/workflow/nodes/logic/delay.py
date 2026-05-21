from app.locales import schema_field_description
import asyncio
from typing import Any, AsyncIterator
from pydantic import BaseModel, Field
from loguru import logger

from ...registry import register_node
from ..base import BaseNode


class LogicDelayInput(BaseModel):
    input: Any = Field(None, description=schema_field_description("input"))
    seconds: float = Field(1.0, description=schema_field_description("seconds"))


class LogicDelayOutput(BaseModel):
    output: Any = Field(None, description=schema_field_description("output"))


@register_node
class LogicDelayNode(BaseNode[LogicDelayInput, LogicDelayOutput]):
    node_type = "Logic.Delay"
    category = "logic"
    label = "Delay"
    description = "Delay for a number of seconds"

    input_model = LogicDelayInput
    output_model = LogicDelayOutput

    async def execute(self, inputs: LogicDelayInput) -> AsyncIterator[LogicDelayOutput]:
        await asyncio.sleep(inputs.seconds)

        yield LogicDelayOutput(output=inputs.input)
