from __future__ import annotations
from app.locales import localized_text
from app.locales import schema_field_description

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

DynamicInfoType = Literal[
    "system_or_cheat",
    "level_or_realm",
    "equipment_or_artifact",
    "knowledge_or_intel",
    "asset_or_territory",
    "skill_or_technique",
    "bloodline_or_physique",
    "mental_goal_snapshot",
]

DYNAMIC_INFO_TYPES: List[str] = [
    "system_or_cheat",
    "level_or_realm",
    "equipment_or_artifact",
    "knowledge_or_intel",
    "asset_or_territory",
    "skill_or_technique",
    "bloodline_or_physique",
    "mental_goal_snapshot",
]

LEGACY_DYNAMIC_INFO_TYPE_TO_KEY: Dict[str, str] = {
    localized_text('hardcoded.schemas_entity_1807f674'): "system_or_cheat",
    localized_text('hardcoded.schemas_entity_021217a2'): "level_or_realm",
    localized_text('hardcoded.schemas_entity_fa3e6938'): "equipment_or_artifact",
    localized_text('hardcoded.schemas_entity_219be0f4'): "knowledge_or_intel",
    localized_text('hardcoded.schemas_entity_74355af9'): "asset_or_territory",
    localized_text('hardcoded.schemas_entity_a0bdd7da'): "skill_or_technique",
    localized_text('hardcoded.schemas_entity_af481ccf'): "bloodline_or_physique",
    localized_text('hardcoded.schemas_entity_3ca544ba'): "mental_goal_snapshot",
}
LEGACY_LIFE_SPAN_TO_KEY: Dict[str, str] = {
    localized_text('hardcoded.schemas_entity_527a5685'): "long_term",
    localized_text('hardcoded.schemas_entity_7a478fdf'): "short_term",
}
LEGACY_ROLE_TYPE_TO_KEY: Dict[str, str] = {
    localized_text('hardcoded.schemas_entity_dd034941'): "protagonist",
    localized_text('hardcoded.schemas_entity_b3c31afe'): "main_cast_support",
    localized_text('hardcoded.schemas_entity_167c6829'): "npc",
    localized_text('hardcoded.schemas_entity_50db58ed'): "antagonist",
}

EntityType = Literal["character", "scene", "organization", "item", "concept"]


class DynamicInfoItem(BaseModel):
    id: int = Field(-1, description=schema_field_description("id"))
    info: str = Field(description=schema_field_description("info"))


class DynamicInfo(BaseModel):
    name: str = Field(description=schema_field_description("name"))
    dynamic_info: Dict[DynamicInfoType, List[DynamicInfoItem]] = Field(
        default_factory=dict,
        description=schema_field_description("dynamic_info"),
    )

    @staticmethod
    def _normalize_dynamic_info_dict(v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            return {}
        normalized: Dict[str, Any] = {}
        allowed = set(DYNAMIC_INFO_TYPES)
        for k, arr in v.items():
            key = k if isinstance(k, str) else str(k)
            key = LEGACY_DYNAMIC_INFO_TYPE_TO_KEY.get(key, key)
            if key in allowed:
                normalized[key] = arr
        return normalized

    @field_validator("dynamic_info", mode="before")
    @classmethod
    def _normalize_keys(cls, v: Any) -> Dict[str, Any]:
        return cls._normalize_dynamic_info_dict(v)


class DeletionInfo(BaseModel):
    name: str = Field(description=schema_field_description("name"))
    dynamic_type: DynamicInfoType = Field(description=schema_field_description("dynamic_type"))
    id: int = Field(gt=0, description=schema_field_description("id"))


class UpdateDynamicInfo(BaseModel):
    info_list: List[DynamicInfo] = Field(description=schema_field_description("info_list"))
    delete_info_list: Optional[List[DeletionInfo]] = Field(default=None, description=schema_field_description("delete_info_list"))


class Entity(BaseModel):
    name: str = Field(..., min_length=1, description=schema_field_description("name"))
    entity_type: EntityType = Field(..., description=schema_field_description("entity_type"))
    life_span: Literal["long_term", "short_term"] = Field(description=schema_field_description("life_span"))



    @field_validator("life_span", mode="before")
    @classmethod
    def _normalize_life_span(cls, value: Any) -> Any:
        if isinstance(value, str):
            return LEGACY_LIFE_SPAN_TO_KEY.get(value, value)
        return value

class CharacterCardCore(Entity):
    last_appearance: Optional[Tuple[int, int]] = Field(default=None, description=schema_field_description("last_appearance"))
    role_type: Literal["protagonist", "main_cast_support", "npc", "antagonist"] = Field("main_cast_support", description=schema_field_description("role_type"))

    @field_validator("role_type", mode="before")
    @classmethod
    def _normalize_role_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            return LEGACY_ROLE_TYPE_TO_KEY.get(value, value)
        return value
    born_scene: str = Field(description=schema_field_description("born_scene"))
    description: str = Field(description=schema_field_description("description"))


class CharacterCard(CharacterCardCore):
    entity_type: EntityType = Field("character", description=schema_field_description("entity_type"))
    personality: str = Field(description=schema_field_description("personality"))
    core_drive: str = Field(description=schema_field_description("core_drive"))
    character_arc: str = Field(description=schema_field_description("character_arc"))
    dynamic_info: Dict[DynamicInfoType, List[DynamicInfoItem]] = Field(
        default_factory=dict,
        description=schema_field_description("dynamic_info"),
    )

    @field_validator("dynamic_info", mode="before")
    @classmethod
    def _normalize_dynamic_info(cls, v: Any) -> Dict[str, Any]:
        return DynamicInfo._normalize_dynamic_info_dict(v)


class SceneCard(Entity):
    entity_type: EntityType = Field("scene", description=schema_field_description("entity_type"))
    description: str = Field(description=schema_field_description("description"))
    function_in_story: str = Field(description=schema_field_description("function_in_story"))
    dynamic_state: List[str] = Field(default_factory=list, description=schema_field_description("dynamic_state"))
    last_appearance: Optional[Tuple[int, int]] = Field(default=None, description=schema_field_description("last_appearance"))


class OrganizationCard(Entity):
    entity_type: EntityType = Field("organization", description=schema_field_description("entity_type"))
    description: str = Field(description=schema_field_description("description"))
    influence: Optional[str] = Field(default=None, description=schema_field_description("influence"))
    relationship: Optional[List[str]] = Field(default=None, description=schema_field_description("relationship"))
    dynamic_state: List[str] = Field(default_factory=list, description=schema_field_description("dynamic_state"))
    last_appearance: Optional[Tuple[int, int]] = Field(default=None, description=schema_field_description("last_appearance"))


class SceneCardMemory(Entity):
    entity_type: EntityType = Field("scene", description="scene entity type")
    life_span: Optional[Literal["long_term", "short_term"]] = Field(default=None, description="scene lifespan")
    description: str = Field(default="", description="scene description")
    function_in_story: str = Field(default="", description="scene function in story")
    dynamic_state: List[str] = Field(default_factory=list, description="scene dynamic state summary")


class OrganizationCardMemory(Entity):
    entity_type: EntityType = Field("organization", description="organization entity type")
    life_span: Optional[Literal["long_term", "short_term"]] = Field(default=None, description="organization lifespan")
    description: str = Field(default="", description="organization description")
    influence: Optional[str] = Field(default=None, description="organization influence")
    relationship: List[str] = Field(default_factory=list, description="organization relationships")
    dynamic_state: List[str] = Field(default_factory=list, description="organization dynamic state summary")


class ItemCard(Entity):
    entity_type: EntityType = Field("item", description=schema_field_description("entity_type"))
    life_span: Literal["long_term", "short_term"] = Field("long_term", description=schema_field_description("life_span"))
    category: str = Field(
        default="",
        description=schema_field_description("category"),
        json_schema_extra={"x-knowledge-source": localized_text('hardcoded.schemas_entity_1d02b0c0')},
    )
    description: str = Field(default="", description=schema_field_description("description"))
    owner_hint: Optional[str] = Field(default=None, description=schema_field_description("owner_hint"))
    power_or_effect: Optional[str] = Field(default=None, description=schema_field_description("power_or_effect"))
    constraints: Optional[str] = Field(default=None, description=schema_field_description("constraints"))
    current_state: Optional[str] = Field(default=None, description=schema_field_description("current_state"))
    important_events: List[str] = Field(default_factory=list, description=schema_field_description("important_events"))

class ConceptCard(Entity):
    entity_type: EntityType = Field("concept", description=schema_field_description("entity_type"))
    life_span: Literal["long_term", "short_term"] = Field("long_term", description=schema_field_description("life_span"))
    category: str = Field(
        default="",
        description=schema_field_description("category"),
        json_schema_extra={"x-knowledge-source": localized_text('hardcoded.schemas_entity_6494d2fb')},
    )
    description: str = Field(default="", description=schema_field_description("description"))
    rule_definition: str = Field(default="", description=schema_field_description("rule_definition"))
    cost: Optional[str] = Field(default=None, description=schema_field_description("cost"))
    counter_relations: List[str] = Field(default_factory=list, description=schema_field_description("counter_relations"))
    mastery_hint: Optional[str] = Field(default=None, description=schema_field_description("mastery_hint"))
    known_by: List[str] = Field(default_factory=list, description=schema_field_description("known_by"))
