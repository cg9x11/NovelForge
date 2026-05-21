
from app.locales import schema_field_description
from typing import Any, Dict, Optional, AsyncIterator
from pydantic import BaseModel, Field
from sqlalchemy.orm.attributes import flag_modified

from app.services.workflow.nodes.base import BaseNode
from app.services.workflow.registry import register_node


class CardUpdateInput(BaseModel):
    card_id: Optional[int] = Field(None, description=schema_field_description("card_id"))
    content_merge: Dict[str, Any] = Field(
        default_factory=dict,
        description=schema_field_description("content_merge")
    )
    title: Optional[str] = Field(
        None,
        description=schema_field_description("title")
    )


class CardUpdateOutput(BaseModel):
    card_id: int = Field(..., description=schema_field_description("card_id"))
    success: bool = Field(True, description=schema_field_description("success"))


@register_node
class CardUpdateNode(BaseNode):


    node_type = "Card.Update"
    category = "card"
    label = "Update Card"
    description = "Update an existing card"

    input_model = CardUpdateInput
    output_model = CardUpdateOutput

    async def execute(self, input_data: CardUpdateInput) -> AsyncIterator[CardUpdateOutput]:
        from sqlmodel import select
        from app.db.models import Card

        card_id = input_data.card_id
        if not card_id:
            raise ValueError("card_id is required")

        card = self.context.session.get(Card, card_id)
        if not card:
            raise ValueError(f"\u5361\u7247\u4e0d\u5b58\u5728: card_id={card_id}")

        if input_data.title:
            card.title = input_data.title

        if input_data.content_merge:
            card.content = self._deep_merge(card.content or {}, input_data.content_merge)
            flag_modified(card, "content")

        self.context.session.add(card)
        self.context.session.commit()
        self.context.session.refresh(card)

        yield CardUpdateOutput(
            card_id=card.id,
            success=True
        )

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result
