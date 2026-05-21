from __future__ import annotations
from app.locales import localized_text
from app.locales import schema_field_description

from typing import List, Optional

from pydantic import BaseModel, Field


class BookStageItem(BaseModel):


    stage_name: str = Field(description=schema_field_description("stage_name"))
    chapter_start: int = Field(description=schema_field_description("chapter_start"), ge=1)
    chapter_end: int = Field(description=schema_field_description("chapter_end"), ge=1)
    stage_outline: str = Field(
        description=(
            localized_text('hardcoded.schemas_workflow_models_75bf2c63')
            + localized_text('hardcoded.schemas_workflow_models_cb8b950c')
            + localized_text('hardcoded.schemas_workflow_models_db67bfde')
        )
    )

    stage_summary: Optional[str] = Field(
        default=None,
        description=schema_field_description("stage_summary"),
    )


class BookStageChunkPlan(BaseModel):


    stages: List[BookStageItem] = Field(
        default_factory=list,
        description=schema_field_description("stages")
    )


class BookStageFinalPlan(BaseModel):


    stages: List[BookStageItem] = Field(
        default_factory=list,
        description=schema_field_description("stages")
    )
