
from app.locales import schema_field_description
from typing import Any, List, Union, AsyncIterator
from pydantic import BaseModel, Field, field_validator

from ...registry import register_node
from ..base import BaseNode


class WaitInput(BaseModel):
    input: Any = Field(None, description=schema_field_description("input"))
    tasks: Union[str, List[str]] = Field(
        ...,
        description=schema_field_description("tasks"),
        json_schema_extra={
            "x-component": "TaskSelect",
            "x-multiple": True
        }
    )

    @field_validator('tasks', mode='before')
    @classmethod
    def normalize_tasks(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class WaitOutput(BaseModel):
    waited_tasks: List[str] = Field(..., description=schema_field_description("waited_tasks"))
    count: int = Field(..., description=schema_field_description("count"))


@register_node
class WaitNode(BaseNode[WaitInput, WaitOutput]):


    node_type = "Logic.Wait"
    category = "logic"
    label = "Wait"
    description = "Wait for another workflow variable or event"

    input_model = WaitInput
    output_model = WaitOutput

    async def execute(self, inputs: WaitInput) -> AsyncIterator[WaitOutput]:
        yield WaitOutput(
            waited_tasks=inputs.tasks,
            count=len(inputs.tasks)
        )
