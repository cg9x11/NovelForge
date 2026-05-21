from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator, Union, TYPE_CHECKING
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select
from sqlalchemy.orm.attributes import flag_modified

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from app.db.models import Card
from app.services.card_service import CardService
from app.schemas.card import CardCreate
from ...registry import register_node
from ..base import BaseNode, get_card_type_by_name


class CardBatchUpsertInput(BaseModel):
    project_id: int = Field(..., description=schema_field_description("project_id"))
    items: List[Any] = Field(..., description=schema_field_description("items"))
    card_type: str = Field(
        ...,
        description=schema_field_description("card_type"),
        json_schema_extra={"x-component": "CardTypeSelect"}
    )
    title_template: str = Field(..., description=schema_field_description("title_template"))
    content_template: Optional[Any] = Field(default_factory=dict, description=schema_field_description("content_template"))
    match_by: str = Field("title", description=schema_field_description("match_by"))
    parent_id: Optional[Any] = Field(None, description=schema_field_description("parent_id"))


class CardBatchUpsertOutput(BaseModel):
    cards: List[Dict[str, Any]] = Field(..., description=schema_field_description("cards"))
    output: List[int] = Field(..., description=schema_field_description("output"))


@register_node
class CardBatchUpsertNode(BaseNode[CardBatchUpsertInput, CardBatchUpsertOutput]):
    node_type = "Card.BatchUpsert"
    category = "card"
    label = "Batch Upsert Cards"
    description = "Create or update cards from a list"

    input_model = CardBatchUpsertInput
    output_model = CardBatchUpsertOutput

    async def execute(self, inputs: CardBatchUpsertInput) -> AsyncIterator[Union['ProgressEvent', CardBatchUpsertOutput]]:
        from ...engine.async_executor import ProgressEvent

        items = inputs.items

        if not isinstance(items, list):
            raise ValueError(f"items \u8f93\u5165\u5fc5\u987b\u662f\u5217\u8868\u7c7b\u578b，\u5f53\u524d\u7c7b\u578b: {type(items).__name__}。\u8bf7\u4f7f\u7528 Data.ExtractPath \u8282\u70b9\u63d0\u53d6\u5217\u8868。")

        checkpoint = getattr(self.context, 'checkpoint', None)
        start_index = checkpoint.get('processed_count', 0) if checkpoint else 0

        if start_index > 0:


            pass
        pass
        base_parent_id = inputs.parent_id

        if isinstance(base_parent_id, dict):
            base_parent_id = base_parent_id.get("id")

        card_type = get_card_type_by_name(self.context.session, inputs.card_type)
        if not card_type:
            raise ValueError(f"\u5361\u7247\u7c7b\u578b\u4e0d\u5b58\u5728: {inputs.card_type}")

        project_id = inputs.project_id

        logger.info(
            f"[BatchUpsert] \u4f7f\u7528\u663e\u5f0f\u4f20\u9012\u7684\u9879\u76eeID: project_id={project_id}"
        )

        results = []
        service = CardService(self.context.session)
        total = len(items)

        for index in range(start_index, total):
            item = items[index]

            ctx = {"item": item, "index": index + 1}

            try:
                title = self._render_template(inputs.title_template, ctx)
            except Exception as e:
                continue

            if not title:
                continue

            current_parent_id = None
            if base_parent_id is not None:
                if isinstance(base_parent_id, int):
                    current_parent_id = base_parent_id
                elif isinstance(base_parent_id, str):
                    if '{' in base_parent_id and '}' in base_parent_id:
                        rendered = self._render_template(base_parent_id, ctx)
                        if rendered and rendered.isdigit():
                            current_parent_id = int(rendered)
                        else:
                            current_parent_id = None
                    elif base_parent_id.isdigit():
                         current_parent_id = int(base_parent_id)

            stmt = select(Card).where(
                Card.project_id == project_id,
                Card.card_type_id == card_type.id,
                Card.title == title
            )
            if current_parent_id:
                stmt = stmt.where(Card.parent_id == current_parent_id)

            existing_card = self.context.session.exec(stmt).first()

            content = {}
            if inputs.content_template:
                rendered_content = self._render_content(inputs.content_template, ctx)
                if isinstance(rendered_content, dict):
                    content = rendered_content
                elif rendered_content:
                    content = {"value": rendered_content}
            elif isinstance(item, dict):
                 content = item

            if existing_card:
                updated = False
                if content:
                    if not isinstance(existing_card.content, dict):
                        existing_card.content = {}
                    existing_card.content.update(content)
                    flag_modified(existing_card, "content")
                    updated = True

                if current_parent_id and existing_card.parent_id != current_parent_id:
                    existing_card.parent_id = current_parent_id
                    updated = True

                if updated:
                    self.context.session.add(existing_card)
                    self.context.session.commit()
                    self.context.session.refresh(existing_card)
                    results.append(existing_card)
                else:
                    results.append(existing_card)
            else:
                try:
                    card_create = CardCreate(
                        title=title,
                        content=content,
                        card_type_id=card_type.id,
                        parent_id=current_parent_id,
                        project_id=project_id
                    )

                    new_card = service.create(card_create, project_id)
                    results.append(new_card)
                except Exception as e:
                    continue

            percent = ((index + 1) / total) * 100
            yield ProgressEvent(
                percent=percent,
                message=f"\u5df2\u5904\u7406 {index + 1}/{total} \u5f20\u5361\u7247",
                data={
                    'processed_count': index + 1,
                    'last_title': title
                }
            )

        self.context.session.commit()

        touched = self.context.variables.setdefault("touched_card_ids", [])
        for card in results:
            self.context.session.refresh(card)
            if card.id not in touched:
                touched.append(card.id)


        yield CardBatchUpsertOutput(
            cards=[
                {
                    "id": c.id,
                    "title": c.title,
                    "content": c.content,
                    "parent_id": c.parent_id
                } for c in results
            ],
            output=[c.id for c in results]
        )

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        import re

        def replace(match):
            path = match.group(1).strip()
            parts = path.split('.')
            value = context
            try:
                for part in parts:
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        value = None
                        break
                return str(value) if value is not None else ""
            except Exception:
                return ""

        return re.sub(r'\{([^}]+)\}', replace, template)

    def _render_content(self, template: Any, context: Dict[str, Any]) -> Any:
        if isinstance(template, str):
            if '{' in template and '}' in template:
                import re
                single_path_match = re.fullmatch(r'\{([^}]+)\}', template)
                if single_path_match:
                    path = single_path_match.group(1).strip()
                    parts = path.split('.')
                    value = context
                    try:
                        for part in parts:
                            if isinstance(value, dict):
                                value = value.get(part)
                            elif hasattr(value, part):
                                value = getattr(value, part)
                            else:
                                value = None
                                break
                        if value is not None:
                            return value
                    except Exception:
                        pass

                return self._render_template(template, context)
            return template
        elif isinstance(template, dict):
            return {k: self._render_content(v, context) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._render_content(v, context) for v in template]
        else:
            return template
