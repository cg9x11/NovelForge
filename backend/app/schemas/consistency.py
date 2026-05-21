from __future__ import annotations
from app.locales import schema_field_description

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CheckRequest(BaseModel):
	text: str = Field(..., description=schema_field_description("text"))
	facts_structured: Optional[Dict[str, Any]] = Field(default=None, description=schema_field_description("facts_structured"))


class Issue(BaseModel):
	type: str
	message: str
	position: List[int] | None = None


class FixSuggestion(BaseModel):
	range: List[int] | None = None
	replacement: str


class CheckResponse(BaseModel):
	issues: List[Issue]
	suggested_fixes: List[FixSuggestion]
