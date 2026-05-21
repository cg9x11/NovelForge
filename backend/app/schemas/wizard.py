from app.locales import schema_field_description
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional, List, Tuple, Any, Union

from .entity import CharacterCard as CharacterCard
from .entity import SceneCard as SceneCard
from .entity import OrganizationCard as OrganizationCard
from .entity import EntityType as EntityType


LEGACY_AUDIENCE_TO_KEY = {"??": "general", "??": "male", "??": "female"}
LEGACY_NARRATIVE_PERSON_TO_KEY = {"????": "first_person", "????": "third_person"}
LEGACY_TAG_WEIGHT_TO_KEY = {"???": "low", "???": "medium", "???": "high"}
LEGACY_STORY_TYPE_TO_KEY = {"??": "mainline", "??": "side"}

class Text(BaseModel):
    content: str = Field(description="Nội dung văn bản bất kỳ, cần dùng hoặc chuyển thành định dạng Markdown")

# --- Schemas for Tags ---

class Tags(BaseModel):
    theme: str = Field(default="", description=schema_field_description("theme"))
    audience: Literal['general', 'male', 'female'] = Field(default='general', description=schema_field_description("audience"))
    narrative_person: Literal['first_person', 'third_person'] = Field(default='third_person', description=schema_field_description("narrative_person"))
    story_tags: List[Tuple[str, Literal['low', 'medium', 'high']]] = Field(default=[], description=schema_field_description("story_tags"))
    affection: str = Field(default="", description=schema_field_description("affection"))

    @field_validator("audience", mode="before")
    @classmethod
    def _normalize_audience(cls, value: Any) -> Any:
        return LEGACY_AUDIENCE_TO_KEY.get(value, value) if isinstance(value, str) else value

    @field_validator("narrative_person", mode="before")
    @classmethod
    def _normalize_narrative_person(cls, value: Any) -> Any:
        return LEGACY_NARRATIVE_PERSON_TO_KEY.get(value, value) if isinstance(value, str) else value

    @field_validator("story_tags", mode="before")
    @classmethod
    def _normalize_story_tags(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [(item[0], LEGACY_TAG_WEIGHT_TO_KEY.get(item[1], item[1])) if isinstance(item, (list, tuple)) and len(item) >= 2 else item for item in value]
        return value


class SpecialAbility(BaseModel):
    name: str = Field(description=schema_field_description("name"))
    description: str = Field(description=schema_field_description("description"))


class SpecialAbilityResponse(BaseModel):
    special_abilities_thinking: str = Field(description=schema_field_description("special_abilities_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    special_abilities: Optional[List[SpecialAbility]] = Field(None, description=schema_field_description("special_abilities"))


class OneSentence(BaseModel):
    one_sentence_thinking: str = Field(description=schema_field_description("one_sentence_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    one_sentence: str = Field(description=schema_field_description("one_sentence"))


class ParagraphOverview(BaseModel):
    overview_thinking: str = Field(description=schema_field_description("overview_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    overview: str = Field(description=schema_field_description("overview"))


class SocialSystem(BaseModel):
    power_structure: str = Field(description=schema_field_description("power_structure"))
    currency_system: List[str] = Field(description=schema_field_description("currency_system"))
    background:List[str]=Field(description=schema_field_description("background"))
    major_power_camps: List[OrganizationCard] = Field(description=schema_field_description("major_power_camps"))
    civilization_level: Optional[str] = Field(description=schema_field_description("civilization_level"))

class CoreSystem(BaseModel):
    system_type: str = Field(min_length=1,description=schema_field_description("system_type"))
    name: str = Field(description=schema_field_description("name"))
    levels: Optional[List[str]] = Field(None, description=schema_field_description("levels"))
    source: str = Field(description=schema_field_description("source"))

class SettingItem(BaseModel):
    title: str = Field(description=schema_field_description("title"))
    description: str = Field(description=schema_field_description("description"))

class WorldviewTemplate(BaseModel):
    world_name: str = Field(min_length=2, description=schema_field_description("world_name"))
    core_conflict: str = Field(description=schema_field_description("core_conflict"))
    social_system: SocialSystem = Field(description=schema_field_description("social_system"))
    power_systems: List[CoreSystem] = Field(description=schema_field_description("power_systems"),max_length=2)
    # key_settings: Optional[List[SettingItem]] = Field(description=schema_field_description("power_systems"))

class WorldBuilding(BaseModel):
    world_view_thinking: str = Field(description=schema_field_description("world_view_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    world_view: WorldviewTemplate


# === Step 3: Blueprint Schemas ===


class Blueprint(BaseModel):
    volume_count: int = Field(description=schema_field_description("volume_count"))
    character_thinking: str = Field(description=schema_field_description("character_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    character_cards: List[CharacterCard] = Field(description=schema_field_description("character_cards"))

    # organization_thinking:str=Field(description=schema_field_description("character_cards"))
    # organization_cards: List[OrganizationCard] = Field(description=schema_field_description("character_cards"))

    scene_thinking: str = Field(description=schema_field_description("scene_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    scene_cards: List[SceneCard] = Field(description=schema_field_description("scene_cards"))


# === Step 4: Volume Outline Schemas===

class CharacterAction(BaseModel):
    name: str = Field(description=schema_field_description("name"))
    description: str = Field(description=schema_field_description("description"))

class StoryLine(BaseModel):
    story_type: Literal['mainline', 'side'] = Field(description=schema_field_description("story_type"))
    name: str = Field(description=schema_field_description("name"))
    overview: str = Field(description=schema_field_description("overview"))


class VolumeOutline(BaseModel):
    volume_number: Optional[int] = Field(description=schema_field_description("volume_number"))
    thinking: Optional[str] = Field(description=schema_field_description("thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    main_target: StoryLine = Field(description=schema_field_description("main_target"))
    branch_line: Optional[List[StoryLine]] = Field(description=schema_field_description("branch_line"))
    character_thinking: Optional[str] = Field(description=schema_field_description("character_thinking"),examples=["V? d? minh h?a c?ch suy ngh?; kh?ng c?n sao ch?p n?i dung c? th?."])
    new_character_cards: Optional[List[CharacterCard]] = Field(default=None, description=schema_field_description("new_character_cards"))
    new_scene_cards: Optional[List[SceneCard]]= Field(default=None, description=schema_field_description("new_scene_cards"))
    # stage_lines: Optional[List[StageLine]] = Field(default=[], description=schema_field_description("new_scene_cards"))
    stage_count:int=Field(description=schema_field_description("stage_count"))
    character_action_list: Optional[List[CharacterAction]] = Field( description=schema_field_description("character_action_list"))
    entity_snapshot: Optional[List[str]] = Field(description=schema_field_description("entity_snapshot"))

class WritingGuide(BaseModel):
    volume_number: int = Field(description=schema_field_description("volume_number"))
    content: str = Field(description=schema_field_description("content"),min_length=100)


class ReviewResultCardContent(BaseModel):
    review_target_card_id: int = Field(description=schema_field_description("review_target_card_id"))
    review_target_title: str = Field(description=schema_field_description("review_target_title"))
    review_target_type: Literal['card'] = Field(default='card', description=schema_field_description("review_target_type"))
    review_type: Literal['chapter', 'stage', 'card', 'custom'] = Field(description=schema_field_description("review_type"))
    review_profile: str = Field(description=schema_field_description("review_profile"))
    review_target_field: Optional[str] = Field(default=None, description=schema_field_description("review_target_field"))
    quality_gate: Literal['pass', 'revise', 'block'] = Field(description=schema_field_description("quality_gate"))
    review_markdown: str = Field(description=schema_field_description("review_markdown"))
    prompt_name: str = Field(description=schema_field_description("prompt_name"))
    llm_config_id: Optional[int] = Field(default=None, description=schema_field_description("llm_config_id"))
    reviewed_at: str = Field(description=schema_field_description("reviewed_at"))
    target_snapshot: Optional[str] = Field(default=None, description=schema_field_description("target_snapshot"))
    meta: Optional[dict[str, Any]] = Field(default_factory=dict, description=schema_field_description("meta"))

class ChapterOutline(BaseModel):
    volume_number: int = Field(description=schema_field_description("volume_number"))
    stage_number:int=Field(description=schema_field_description("stage_number"))
    title: str= Field(description=schema_field_description("title"))
    chapter_number: int = Field(description=schema_field_description("chapter_number"))

    overview: str = Field(description=schema_field_description("overview"),min_length=100)
    entity_list: List[str] = Field(
        description=schema_field_description("entity_list"),
    )



class StageLine(BaseModel):
    volume_number:int=Field(description=schema_field_description("volume_number"))
    stage_number:int=Field(description=schema_field_description("stage_number"))
    stage_name: str = Field(description=schema_field_description("stage_name"))
    reference_chapter: Tuple[int, int] = Field(description=schema_field_description("reference_chapter"))
    analysis: Optional[str] = Field(description=schema_field_description("analysis"))
    overview: Optional[str] = Field(description=schema_field_description("overview"))
    chapter_outline_list:Optional[List[ChapterOutline]]=Field(description=schema_field_description("chapter_outline_list"))
    entity_snapshot: Optional[List[str]] = Field(description=schema_field_description("entity_snapshot"))
    @model_validator(mode="after")
    def validate_chapter_outline_coverage(self):
        # Allow empty list for workflow post-processing cleanup.
        if not self.chapter_outline_list:
            return self

        start, end = self.reference_chapter
        if start > end:
            raise ValueError("reference_chapter start must be <= end")

        actual_numbers = [item.chapter_number for item in self.chapter_outline_list]
        expected_numbers = list(range(start, end + 1))
        if actual_numbers != expected_numbers:
            raise ValueError(
                "chapter_outline_list.chapter_number must be contiguous and fully cover reference_chapter"
            )
        return self


# === Step 6: Batch Chapter Outline Schemas===

class Chapter(BaseModel):
    volume_number: int = Field( description=schema_field_description("volume_number"))
    stage_number: int=Field(description=schema_field_description("stage_number"))
    title: str = Field(description=schema_field_description("title"))
    chapter_number: int = Field(description=schema_field_description("chapter_number"))

    entity_list: List[str] = Field(
        description=schema_field_description("entity_list"),
    )
    content:Optional[str]=Field(default="",description=schema_field_description("content"))


