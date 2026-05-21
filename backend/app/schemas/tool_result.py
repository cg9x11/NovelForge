from app.locales import schema_field_description
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"
    CONFIRMATION_REQUIRED = "confirmation_required"


class ToolResult(BaseModel):
    success: bool = Field(description=schema_field_description("success"))
    status: ToolResultStatus = Field(
        default=ToolResultStatus.SUCCESS,
        description=schema_field_description("status")
    )
    message: str = Field(description=schema_field_description("message"))

    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description=schema_field_description("data")
    )
    error: Optional[str] = Field(
        default=None,
        description=schema_field_description("error")
    )

    class Config:
        use_enum_values = True


class ConfirmationRequest(ToolResult):
    success: bool = False
    status: ToolResultStatus = ToolResultStatus.CONFIRMATION_REQUIRED

    confirmation_id: str = Field(description=schema_field_description("confirmation_id"))
    action: str = Field(description=schema_field_description("action"))
    action_params: Dict[str, Any] = Field(description=schema_field_description("action_params"))
    warning: Optional[str] = Field(
        default=None,
        description=schema_field_description("warning")
    )

    class Config:
        use_enum_values = True


class CardOperationResult(ToolResult):
    card_id: Optional[int] = Field(default=None, description=schema_field_description("card_id"))
    card_title: Optional[str] = Field(default=None, description=schema_field_description("card_title"))
    card_type: Optional[str] = Field(default=None, description=schema_field_description("card_type"))

    needs_confirmation: Optional[bool] = Field(
        default=None,
        description=schema_field_description("needs_confirmation")
    )

    current_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description=schema_field_description("current_data")
    )
    missing_fields: Optional[List[str]] = Field(
        default=None,
        description=schema_field_description("missing_fields")
    )
    applied: Optional[int] = Field(
        default=None,
        description=schema_field_description("applied")
    )
    failed: Optional[int] = Field(
        default=None,
        description=schema_field_description("failed")
    )

    class Config:
        use_enum_values = True


class CardSearchResult(ToolResult):
    total: int = Field(default=0, description=schema_field_description("total"))
    cards: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=schema_field_description("cards")
    )

    class Config:
        use_enum_values = True


def to_dict(result: ToolResult) -> Dict[str, Any]:
    return result.model_dump(exclude_none=True, mode='json')
