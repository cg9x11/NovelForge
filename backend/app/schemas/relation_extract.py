from __future__ import annotations
from app.locales import localized_text
from app.locales import schema_field_description

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator



RelationKind = Literal[
    'ally', 'team', 'fellow', 'enemy', 'family', 'mentor', 'rival', 'partner', 'superior', 'subordinate', 'guide',
    'member_of', 'member', 'lead', 'found',
    'own', 'use', 'practice', 'realize', 'carry', 'map_to',
    'control', 'locate_in',
    'influence', 'counter', 'about', 'other'
]
RelationStance = Literal['friendly', 'neutral', 'hostile']
RELATION_STANCES: tuple[RelationStance, ...] = ('friendly', 'neutral', 'hostile')

CN_TO_EN_KIND: Dict[str, str] = {
    localized_text('hardcoded.schemas_relation_extract_e099cf3a'): 'ally',
    localized_text('hardcoded.schemas_relation_extract_1714e8e2'): 'team',
    localized_text('hardcoded.schemas_relation_extract_39c522bc'): 'fellow',
    localized_text('hardcoded.schemas_relation_extract_64dfc6f1'): 'enemy',
    localized_text('hardcoded.schemas_relation_extract_957300ee'): 'family',
    localized_text('hardcoded.schemas_relation_extract_e498942f'): 'mentor',
    localized_text('hardcoded.schemas_relation_extract_4f76b088'): 'rival',
    localized_text('hardcoded.schemas_relation_extract_d9898a35'): 'partner',
    localized_text('hardcoded.schemas_relation_extract_20530078'): 'superior',
    localized_text('hardcoded.schemas_relation_extract_a969cc1d'): 'subordinate',
    localized_text('hardcoded.schemas_relation_extract_7985123f'): 'guide',
    localized_text('hardcoded.schemas_relation_extract_714977c6'): 'member_of',
    localized_text('hardcoded.schemas_relation_extract_c1ee9f01'): 'member',
    localized_text('hardcoded.schemas_relation_extract_ec60df3d'): 'lead',
    localized_text('hardcoded.schemas_relation_extract_fdc14848'): 'found',
    localized_text('hardcoded.schemas_relation_extract_0121f116'): 'own',
    localized_text('hardcoded.schemas_relation_extract_0e2d3a3c'): 'use',
    localized_text('hardcoded.schemas_relation_extract_b8f7af2e'): 'practice',
    localized_text('hardcoded.schemas_relation_extract_71e4ce1f'): 'realize',
    localized_text('hardcoded.schemas_relation_extract_f7e680b3'): 'carry',
    localized_text('hardcoded.schemas_relation_extract_43353e02'): 'map_to',
    localized_text('hardcoded.schemas_relation_extract_22382630'): 'control',
    localized_text('hardcoded.schemas_relation_extract_e791961b'): 'locate_in',
    localized_text('hardcoded.schemas_relation_extract_5be321f3'): 'influence',
    localized_text('hardcoded.schemas_relation_extract_bbd32a5e'): 'counter',
    localized_text('hardcoded.schemas_relation_extract_bed172ef'): 'about',
    localized_text('hardcoded.schemas_relation_extract_1a26edf9'): 'other',
}
CN_TO_EN_STANCE: Dict[str, str] = {
    localized_text('hardcoded.schemas_relation_extract_161633de'): 'friendly',
    localized_text('hardcoded.schemas_relation_extract_13baf255'): 'neutral',
    localized_text('hardcoded.schemas_relation_extract_66073845'): 'hostile',
}
EN_TO_CN_KIND: Dict[str, str] = {v: k for k, v in CN_TO_EN_KIND.items()}


class RecentEventSummary(BaseModel):
    summary: str = Field(description=schema_field_description("summary"))
    volume_number: Optional[int] = Field(default=None, description=schema_field_description("volume_number"))
    chapter_number: Optional[int] = Field(default=None, description=schema_field_description("chapter_number"))


class RelationItem(BaseModel):
    a: str = Field(description=schema_field_description("a"))
    b: str = Field(description=schema_field_description("b"))
    kind: RelationKind = Field(description=schema_field_description("kind"))
    description: Optional[str] = Field(default=None, description=schema_field_description("description"))

    @field_validator("kind", mode="before")
    @classmethod
    def _normalize_kind(cls, value: str) -> str:
        return CN_TO_EN_KIND.get(value, value) if isinstance(value, str) else value
    a_to_b_addressing: Optional[str] = Field(default=None, description=schema_field_description("a_to_b_addressing"))
    b_to_a_addressing: Optional[str] = Field(default=None, description=schema_field_description("b_to_a_addressing"))
    recent_dialogues: List[str] = Field(default_factory=list, description=schema_field_description("recent_dialogues"))
    recent_event_summaries: List[RecentEventSummary] = Field(default_factory=list, description=schema_field_description("recent_event_summaries"))
    stance: Optional[RelationStance] = Field(default=None, description=schema_field_description("stance"))

    @field_validator("stance", mode="before")
    @classmethod
    def _normalize_stance(cls, value: str | None) -> str | None:
        return CN_TO_EN_STANCE.get(value, value) if isinstance(value, str) else value


class RelationExtraction(BaseModel):
    relations: List[RelationItem] = Field(default_factory=list)
