from app.locales import schema_field_description
from typing import Any, Dict, Optional, AsyncIterator
from loguru import logger
from pydantic import BaseModel, Field

from app.db.models import Card
from ...registry import register_node
from ..base import BaseNode, get_card_type_by_name


class CardCreateInput(BaseModel):
    project_id: int = Field(..., description=schema_field_description("project_id"))
    card_type: str = Field(..., description=schema_field_description("card_type"))
    title: str = Field(..., description=schema_field_description("title"))
    content: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("content"))
    parent: Optional[Dict[str, Any]] = Field(None, description=schema_field_description("parent"))


class CardCreateOutput(BaseModel):
    id: int = Field(..., description=schema_field_description("id"))
    title: str = Field(..., description=schema_field_description("title"))
    content: Dict[str, Any] = Field(..., description=schema_field_description("content"))
    card_type_id: int = Field(..., description=schema_field_description("card_type_id"))
    parent_id: Optional[int] = Field(None, description=schema_field_description("parent_id"))


@register_node
class CardCreateNode(BaseNode[CardCreateInput, CardCreateOutput]):
    node_type = "Card.Create"
    category = "card"
    label = "Create Card"
    description = "Create a new card"

    input_model = CardCreateInput
    output_model = CardCreateOutput

    async def execute(self, inputs: CardCreateInput) -> AsyncIterator[CardCreateOutput]:
        title = inputs.title
        if not title:
            raise ValueError("Card title is required")

        content = inputs.content or {}

        card_type = get_card_type_by_name(self.context.session, inputs.card_type)
        if not card_type:
            raise ValueError(f"\u5361\u7247\u7c7b\u578b\u4e0d\u5b58\u5728: {inputs.card_type}")

        project_id = inputs.project_id

        parent_data = inputs.parent or {}
        parent_id = parent_data.get("id")

        from app.services.card_service import CardService
        from app.schemas.card import CardCreate

        card_service = CardService(self.context.session)

        try:
            card_in = CardCreate(
                title=title,
                content=content,
                card_type_id=card_type.id,
                parent_id=parent_id,
                project_id=project_id
            )
            card = card_service.create(card_in, project_id)

        except Exception as e:
            logger.error(f"[Card.Create] Create failed: {e}")
            raise

        touched = self.context.variables.setdefault("touched_card_ids", [])
        if card.id not in touched:
            touched.append(card.id)

        logger.info(
            f"[Card.Create] \u521b\u5efa\u5361\u7247: id={card.id}, title={card.title}, "
            f"type={inputs.card_type}"
        )

        yield CardCreateOutput(
            id=card.id,
            title=card.title,
            content=card.content,
            card_type_id=card.card_type_id,
            parent_id=card.parent_id
        )
