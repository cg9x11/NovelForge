
from app.locales import schema_field_description
from typing import Any, Dict, Optional, AsyncIterator
from loguru import logger
from pydantic import BaseModel, Field

from app.services.card_service import CardService
from ...registry import register_node
from ..base import BaseNode


# ============================================================
# Input/Output Models
# ============================================================

class ReplaceTextInput(BaseModel):
    card_id: int = Field(..., description=schema_field_description("card_id"), gt=0)
    field_path: str = Field(..., description=schema_field_description("field_path"))
    old_text: str = Field(..., description=schema_field_description("old_text"))
    new_text: str = Field("", description=schema_field_description("new_text"))


class ReplaceTextOutput(BaseModel):
    card: Dict[str, Any] = Field(..., description=schema_field_description("card"))
    replaced_count: int = Field(..., description=schema_field_description("replaced_count"))
    success: bool = Field(..., description=schema_field_description("success"))


# ============================================================
# Node Implementation
# ============================================================

@register_node
class CardReplaceTextNode(BaseNode[ReplaceTextInput, ReplaceTextOutput]):
    node_type = "Card.ReplaceFieldText"
    category = "card"
    label = "Replace Text"
    description = "Replace text inside a card field"

    input_model = ReplaceTextInput
    output_model = ReplaceTextOutput

    async def execute(self, input_data: ReplaceTextInput) -> AsyncIterator[ReplaceTextOutput]:

        service = CardService(self.context.session)
        result = service.replace_field_text(
            card_id=input_data.card_id,
            field_path=input_data.field_path,
            old_text=input_data.old_text,
            new_text=input_data.new_text,
            fuzzy_match=True
        )

        if not result["success"]:
            raise ValueError(result.get("error", "Replace failed"))

        touched = self.context.variables.setdefault("touched_card_ids", [])
        if input_data.card_id not in touched:
            touched.append(input_data.card_id)

        updated_card = self.get_card_by_id(input_data.card_id)

        yield ReplaceTextOutput(
            card=updated_card,
            replaced_count=result.get("replaced_count", 0),
            success=True
        )

