from __future__ import annotations
from app.locales import localized_text

from typing import Any

from app.db.models import Card
from app.schemas.entity import SceneCard, SceneCardMemory
from app.schemas.memory import SceneStateExtraction
from app.services.memory_extractors.memory_base import (
    StructuredCardExtractorSpec,
    StructuredCardMemoryExtractor,
    merge_optional_text,
    unique_keep_order,
)


def _merge_scene_card(existing: SceneCard, incoming: SceneCardMemory) -> SceneCard:
    return SceneCard(
        name=incoming.name or existing.name,
        entity_type="scene",
        life_span=incoming.life_span or existing.life_span,
        description=merge_optional_text(existing.description, incoming.description) or "",
        function_in_story=merge_optional_text(existing.function_in_story, incoming.function_in_story) or "",
        dynamic_state=unique_keep_order([*(existing.dynamic_state or []), *(incoming.dynamic_state or [])])[-8:],
        last_appearance=existing.last_appearance,
    )


def _load_existing_scene_card(card: Card) -> SceneCard:
    payload = dict(card.content or {})
    payload.setdefault("name", card.title)
    payload.setdefault("entity_type", "scene")
    payload.setdefault("life_span", localized_text('hardcoded.services_memory_extractors_scene_state_527a5685'))
    payload["description"] = payload.get("description") or ""
    payload["function_in_story"] = payload.get("function_in_story") or ""
    if not isinstance(payload.get("dynamic_state"), list):
        payload["dynamic_state"] = []
    return SceneCard.model_validate(payload)


_SPEC = StructuredCardExtractorSpec(
    code="scene_state",
    name="scene_state_extraction",
    prompt_name="scene_state_extraction",
    card_type_name="scene_card",
    output_model=SceneStateExtraction,
    list_field_name="scenes",
    target_participant_types=("scene",),
    related_participant_types=("organization", "character", "item", "concept"),
    target_participant_key="scene_names",
    related_participant_key="related_entities",
    reference_title="Field",
)


class SceneStateExtractor(StructuredCardMemoryExtractor):
    def __init__(self):
        super().__init__(_SPEC)

    def load_existing_card(self, card: Card) -> SceneCard:
        return _load_existing_scene_card(card)

    def merge_card(self, existing: SceneCard, incoming: SceneCardMemory) -> SceneCard:
        return _merge_scene_card(existing, incoming)

    def build_reference_lines(self, model: SceneCard) -> list[str]:
        return [
            f"- {model.name}",
            localized_text('hardcoded.services_memory_extractors_scene_state_c948ca4f'),
            localized_text('hardcoded.services_memory_extractors_scene_state_4a60afa1'),
            localized_text('hardcoded.services_memory_extractors_scene_state_ef9af212'),
        ]
