from app.locales import schema_field_description
from typing import Any, Dict, AsyncIterator
from loguru import logger
from pydantic import BaseModel, Field

from ...registry import register_node
from ..base import BaseNode


class CardDeleteInput(BaseModel):
    card: Dict[str, Any] = Field(..., description=schema_field_description("card"))


class CardDeleteOutput(BaseModel):
    success: bool = Field(..., description=schema_field_description("success"))


@register_node
class CardDeleteNode(BaseNode[CardDeleteInput, CardDeleteOutput]):
    node_type = "Card.Delete"
    category = "card"
    label = "Delete Card"
    description = "Delete a card"

    input_model = CardDeleteInput
    output_model = CardDeleteOutput

    async def execute(self, inputs: CardDeleteInput) -> AsyncIterator[CardDeleteOutput]:
        card_id = inputs.card.get("id")

        if not card_id:
            raise ValueError("Card ID is required")

        from ..base import get_card_by_id
        card = get_card_by_id(self.context.session, card_id)
        if not card:
            raise ValueError(f"\u5361\u7247\u4e0d\u5b58\u5728: {card_id}")

        self.context.session.delete(card)
        self.context.session.commit()


        yield CardDeleteOutput(success=True)
