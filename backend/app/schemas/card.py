from app.locales import localized_text
from app.locales import schema_field_description
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


# --- CardType Schemas ---

class CardTypeBase(BaseModel):
    key: Optional[str] = None
    name: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None
    ai_params: Optional[Dict[str, Any]] = None
    editor_component: Optional[str] = None
    is_ai_enabled: bool = Field(default=False)
    is_singleton: bool = Field(default=False)
    default_ai_context_template: Optional[str] = None
    default_ai_context_template_review: Optional[str] = None
    ui_layout: Optional[Dict[str, Any]] = None


class CardTypeCreate(CardTypeBase):
    pass


class CardTypeUpdate(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None
    ai_params: Optional[Dict[str, Any]] = None
    editor_component: Optional[str] = None
    is_ai_enabled: Optional[bool] = None
    is_singleton: Optional[bool] = None
    default_ai_context_template: Optional[str] = None
    default_ai_context_template_review: Optional[str] = None
    ui_layout: Optional[Dict[str, Any]] = None


class CardTypeRead(CardTypeBase):
    id: int
    built_in: bool = False


# --- Card Schemas ---

class CardBase(BaseModel):
    title: str
    model_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parent_id: Optional[int] = None
    card_type_id: int
    json_schema: Optional[Dict[str, Any]] = None
    ai_params: Optional[Dict[str, Any]] = None
    ai_context_template: Optional[str] = None
    ai_context_template_review: Optional[str] = None


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: Optional[str] = None
    model_name: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None
    display_order: Optional[int] = None
    ai_context_template: Optional[str] = None
    ai_context_template_review: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None
    ai_params: Optional[Dict[str, Any]] = None
    needs_confirmation: Optional[bool] = None


class CardRead(CardBase):
    id: int
    project_id: int
    created_at: datetime
    display_order: int
    card_type: CardTypeRead
    ai_context_template: Optional[str] = None
    ai_context_template_review: Optional[str] = None
    ai_modified: bool = False
    needs_confirmation: bool = False
    last_modified_by: Optional[str] = None


# --- Operations ---

class CardCopyOrMoveRequest(BaseModel):
    target_project_id: int
    parent_id: Optional[int] = None


class CardOrderItem(BaseModel):
    card_id: int
    display_order: int
    parent_id: Optional[int] = None


class CardBatchReorderRequest(BaseModel):
    updates: List[CardOrderItem] = Field(description=schema_field_description("updates"))


# --- Export ---

CardExportScope = Literal["all", "single", "type"]
CardExportFormat = Literal["txt", "md", "json"]


class CardExportRequest(BaseModel):


    scope: CardExportScope = Field(default="all", description=schema_field_description("scope"))
    card_id: Optional[int] = Field(default=None, description=schema_field_description("card_id"))
    card_type_id: Optional[int] = Field(default=None, description=schema_field_description("card_type_id"))
    format: CardExportFormat = Field(default="txt", description=schema_field_description("format"))

    @model_validator(mode="after")
    def validate_scope_fields(self):
        if self.scope == "single" and self.card_id is None:
            raise ValueError(localized_text('hardcoded.schemas_card_80b22cb0'))
        if self.scope == "type" and self.card_type_id is None:
            raise ValueError(localized_text('hardcoded.schemas_card_2225cd5e'))
        return self
