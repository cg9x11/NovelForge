from __future__ import annotations
from app.locales import schema_field_description

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.relation_extract import RelationItem


class AssembleContextRequest(BaseModel):
	project_id: Optional[int] = Field(default=None, description=schema_field_description("project_id"))
	volume_number: Optional[int] = Field(default=None, description=schema_field_description("volume_number"))
	chapter_number: Optional[int] = Field(default=None, description=schema_field_description("chapter_number"))
	chapter_id: Optional[int] = Field(default=None, description=schema_field_description("chapter_id"))
	participants: Optional[List[str]] = Field(default=None, description=schema_field_description("participants"))
	current_draft_tail: Optional[str] = Field(default=None, description=schema_field_description("current_draft_tail"))
	recent_chapters_window: Optional[int] = Field(default=None, description=schema_field_description("recent_chapters_window"))


class ItemSummary(BaseModel):
	name: str = Field(..., description=schema_field_description("name"))
	category: str = Field(default="", description=schema_field_description("category"))
	description: str = Field(default="", description=schema_field_description("description"))
	owner_hint: Optional[str] = Field(default=None, description=schema_field_description("owner_hint"))
	current_state: Optional[str] = Field(default=None, description=schema_field_description("current_state"))
	power_or_effect: Optional[str] = Field(default=None, description=schema_field_description("power_or_effect"))
	constraints: Optional[str] = Field(default=None, description=schema_field_description("constraints"))
	important_events: List[str] = Field(default_factory=list, description=schema_field_description("important_events"))


class ConceptSummary(BaseModel):
	name: str = Field(..., description=schema_field_description("name"))
	category: str = Field(default="", description=schema_field_description("category"))
	description: str = Field(default="", description=schema_field_description("description"))
	rule_definition: str = Field(default="", description=schema_field_description("rule_definition"))
	cost: Optional[str] = Field(default=None, description=schema_field_description("cost"))
	mastery_hint: Optional[str] = Field(default=None, description=schema_field_description("mastery_hint"))
	known_by: List[str] = Field(default_factory=list, description=schema_field_description("known_by"))
	counter_relations: List[str] = Field(default_factory=list, description=schema_field_description("counter_relations"))


class FactsStructured(BaseModel):
	fact_summaries: List[str] = Field(default_factory=list, description=schema_field_description("fact_summaries"))
	relation_summaries: List[RelationItem] = Field(default_factory=list, description=schema_field_description("relation_summaries"))
	item_summaries: List[ItemSummary] = Field(default_factory=list, description=schema_field_description("item_summaries"))
	concept_summaries: List[ConceptSummary] = Field(default_factory=list, description=schema_field_description("concept_summaries"))


class AssembleContextResponse(BaseModel):
	facts_subgraph: str = Field(default="", description=schema_field_description("facts_subgraph"))
	budget_stats: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("budget_stats"))
	facts_structured: Optional[FactsStructured] = Field(default=None, description=schema_field_description("facts_structured"))


class ContextSettingsModel(BaseModel):
	recent_chapters_window: int
	total_context_budget_chars: int
	soft_budget_chars: int
	quota_recent: int
	quota_older_summary: int
	quota_facts: int


class UpdateContextSettingsRequest(BaseModel):
	recent_chapters_window: Optional[int] = None
	total_context_budget_chars: Optional[int] = None
	soft_budget_chars: Optional[int] = None
	quota_recent: Optional[int] = None
	quota_older_summary: Optional[int] = None
	quota_facts: Optional[int] = None
