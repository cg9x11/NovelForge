from app.locales import schema_field_description
from typing import Optional
from pydantic import BaseModel, Field

from ..base import BaseNode
from ...registry import register_node


class TriggerProjectCreatedInput(BaseModel):
    template: Optional[str] = Field(
        None,
        description=schema_field_description("template")
    )


class TriggerProjectCreatedOutput(BaseModel):
    project_id: int = Field(..., description=schema_field_description("project_id"))
    template: Optional[str] = Field(None, description=schema_field_description("template"))


@register_node
class TriggerProjectCreatedNode(BaseNode):


    node_type = "Trigger.ProjectCreated"
    category = "trigger"
    label = "Project Created Trigger"
    description = "Trigger when a project is created"

    input_model = TriggerProjectCreatedInput
    output_model = TriggerProjectCreatedOutput

    async def execute(self, inputs: TriggerProjectCreatedInput):
        trigger_data = self.context.variables.get("__trigger_data__", {})

        yield TriggerProjectCreatedOutput(
            project_id=trigger_data.get("project_id"),
            template=trigger_data.get("template")
        )
