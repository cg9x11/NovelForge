from app.locales import schema_field_description
from typing import Optional
from pydantic import BaseModel, Field

from ..base import BaseNode
from ...registry import register_node


class TriggerCardSavedInput(BaseModel):
    card_type: Optional[str] = Field(
        None,
        description=schema_field_description("card_type")
    )
    on_create: bool = Field(
        False,
        description=schema_field_description("on_create")
    )
    on_update: bool = Field(
        True,
        description=schema_field_description("on_update")
    )


class TriggerCardSavedOutput(BaseModel):
    card_id: int = Field(..., description=schema_field_description("card_id"))
    project_id: int = Field(..., description=schema_field_description("project_id"))
    card_type: Optional[str] = Field(None, description=schema_field_description("card_type"))
    is_created: bool = Field(..., description=schema_field_description("is_created"))


@register_node
class TriggerCardSavedNode(BaseNode):


    node_type = "Trigger.CardSaved"
    category = "trigger"
    label = "Card Saved Trigger"
    description = "Trigger when a card is saved"

    input_model = TriggerCardSavedInput
    output_model = TriggerCardSavedOutput

    async def execute(self, inputs: TriggerCardSavedInput):
        trigger_data = self.context.variables.get("__trigger_data__", {})

        card_type = trigger_data.get("card_type")
        if card_type is None:
            card_type = inputs.card_type

        yield TriggerCardSavedOutput(
            card_id=trigger_data.get("card_id"),
            project_id=trigger_data.get("project_id"),
            card_type=card_type,
            is_created=trigger_data.get("is_created", False)
        )
