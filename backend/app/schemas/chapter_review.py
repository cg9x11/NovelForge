from app.locales import schema_field_description
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


QualityGate = Literal["pass", "revise", "block"]
ReviewType = Literal["chapter", "stage", "card", "custom"]
TargetType = Literal["card"]


class ReviewResultCardContent(BaseModel):
    review_target_card_id: int = Field(description=schema_field_description("review_target_card_id"))
    review_target_title: str = Field(description=schema_field_description("review_target_title"))
    review_target_type: TargetType = Field(default="card", description=schema_field_description("review_target_type"))
    review_type: ReviewType = Field(default="card", description=schema_field_description("review_type"))
    review_profile: str = Field(description=schema_field_description("review_profile"))
    review_target_field: Optional[str] = Field(default=None, description=schema_field_description("review_target_field"))
    quality_gate: QualityGate = Field(description=schema_field_description("quality_gate"))
    review_markdown: str = Field(description=schema_field_description("review_markdown"))
    prompt_name: str = Field(description=schema_field_description("prompt_name"))
    llm_config_id: Optional[int] = Field(default=None, description=schema_field_description("llm_config_id"))
    reviewed_at: str = Field(description=schema_field_description("reviewed_at"))
    target_snapshot: Optional[str] = Field(default=None, description=schema_field_description("target_snapshot"))
    meta: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("meta"))


class ReviewResultCardRead(BaseModel):
    card_id: int
    project_id: int
    title: str
    review_target_card_id: int
    review_target_title: str
    review_target_type: TargetType = "card"
    review_type: ReviewType
    review_profile: str
    review_target_field: Optional[str] = None
    quality_gate: QualityGate
    review_markdown: str
    prompt_name: str
    llm_config_id: Optional[int] = None
    reviewed_at: str
    target_snapshot: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ReviewDraftResult(BaseModel):
    review_text: str
    quality_gate: QualityGate
    review_type: ReviewType
    review_profile: str
    review_target_field: Optional[str] = None
    prompt_name: str
    llm_config_id: Optional[int] = None
    target_snapshot: Optional[str] = None
    existing_review_card_id: Optional[int] = None
    review_card_title: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReviewRunRequest(BaseModel):
    card_id: int
    project_id: Optional[int] = None
    title: str
    target_type: TargetType = Field(default="card")
    review_type: ReviewType = Field(default="card")
    review_profile: str = Field(default="generic_card_review")
    target_field: str = Field(default="content")
    target_text: Optional[str] = None
    context_info: Optional[str] = None
    facts_info: Optional[str] = None
    content_snapshot: Optional[str] = Field(default=None, description=schema_field_description("content_snapshot"))
    llm_config_id: int
    prompt_name: str = Field(default="general_review")
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[float] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReviewCardUpsertRequest(BaseModel):
    project_id: int
    target_card_id: int
    target_title: str
    review_type: ReviewType
    review_profile: str
    target_field: Optional[str] = None
    review_text: str
    quality_gate: QualityGate
    prompt_name: str
    llm_config_id: Optional[int] = None
    content_snapshot: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ReviewRunResponse(BaseModel):
    review_text: str
    draft: ReviewDraftResult
