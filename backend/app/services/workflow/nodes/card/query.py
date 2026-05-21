from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import Card
from ...registry import register_node
from ..base import BaseNode, get_card_type_by_name


class CardQueryInput(BaseModel):
    card_type: Optional[str] = Field(None, description=schema_field_description("card_type"))
    parent_id: Optional[int] = Field(None, description=schema_field_description("parent_id"))
    project_id: Optional[int] = Field(None, description=schema_field_description("project_id"))
    limit: int = Field(100, description=schema_field_description("limit"))


class CardQueryOutput(BaseModel):
    cards: List[Dict[str, Any]] = Field(..., description=schema_field_description("cards"))


@register_node
class CardQueryNode(BaseNode[CardQueryInput, CardQueryOutput]):
    node_type = "Card.Query"
    category = "card"
    label = "Query Cards"
    description = "Query cards by filters"

    input_model = CardQueryInput
    output_model = CardQueryOutput

    async def execute(self, inputs: CardQueryInput) -> AsyncIterator[CardQueryOutput]:
        stmt = select(Card)

        if inputs.card_type:
            card_type = get_card_type_by_name(self.context.session, inputs.card_type)
            if card_type:
                stmt = stmt.where(Card.card_type_id == card_type.id)

        # Parent ID
        if inputs.parent_id is not None:
            stmt = stmt.where(Card.parent_id == inputs.parent_id)

        if inputs.project_id:
            stmt = stmt.where(Card.project_id == inputs.project_id)

        stmt = stmt.limit(inputs.limit)

        cards = list(self.context.session.exec(stmt).all())

        logger.info(
            f"[Card.Query] \u67e5\u8be2\u5361\u7247: type={inputs.card_type}, "
            f"parent_id={inputs.parent_id}, \u7ed3\u679c\u6570={len(cards)}"
        )

        yield CardQueryOutput(
            cards=[
                {
                    "id": card.id,
                    "title": card.title,
                    "content": card.content,
                    "card_type_id": card.card_type_id,
                    "parent_id": card.parent_id
                }
                for card in cards
            ]
        )
