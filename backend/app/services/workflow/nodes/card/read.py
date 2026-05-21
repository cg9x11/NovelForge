from app.locales import schema_field_description
from typing import Any, Dict, Optional, AsyncIterator
from loguru import logger
from pydantic import BaseModel, Field

from app.db.models import Card
from ...registry import register_node
from ..base import BaseNode, get_card_type_by_name, resolve_card_reference


class CardReadInput(BaseModel):
    target: Optional[Any] = Field("$self", description=schema_field_description("target"))
    card_id: Optional[int] = Field(None, description=schema_field_description("card_id"))
    type_name: Optional[str] = Field(None, description=schema_field_description("type_name"))


class CardReadOutput(BaseModel):
    id: int = Field(..., description=schema_field_description("id"))
    title: str = Field(..., description=schema_field_description("title"))
    content: Dict[str, Any] = Field(..., description=schema_field_description("content"))
    card_type_id: int = Field(..., description=schema_field_description("card_type_id"))
    parent_id: Optional[int] = Field(None, description=schema_field_description("parent_id"))


@register_node
class CardReadNode(BaseNode[CardReadInput, CardReadOutput]):
    node_type = "Card.Read"
    category = "card"
    label = "Read Card"
    description = "Read card content"

    input_model = CardReadInput
    output_model = CardReadOutput

    async def execute(self, inputs: CardReadInput) -> AsyncIterator[CardReadOutput]:
        target = inputs.card_id if inputs.card_id is not None else inputs.target

        card = None
        if isinstance(target, int):
            from ..base import get_card_by_id
            card = get_card_by_id(self.context.session, target)
        else:
            card = resolve_card_reference(
                self.context.session,
                target,
                self.context.variables.get("card_id")
            )

            if not card and isinstance(target, str) and target.isdigit():
                from ..base import get_card_by_id
                card = get_card_by_id(self.context.session, int(target))

        if not card:
            raise ValueError(f"\u672a\u627e\u5230\u5361\u7247: {target}")

        touched = self.context.variables.setdefault("touched_card_ids", [])
        if card.id not in touched:
            touched.append(card.id)

        card_type_info = None
        if inputs.type_name:
            card_type = get_card_type_by_name(self.context.session, inputs.type_name)
            if card_type:
                card_type_info = {
                    "id": card_type.id,
                    "name": card_type.name,
                    "schema": card_type.json_schema
                }

        logger.info(
            f"[Card.Read] \u8bfb\u53d6\u5361\u7247: id={card.id}, title={card.title}"
        )

        yield CardReadOutput(
            id=card.id,
            title=card.title,
            content=card.content,
            card_type_id=card.card_type_id,
            parent_id=card.parent_id
        )
