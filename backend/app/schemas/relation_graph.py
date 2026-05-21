from __future__ import annotations
from app.locales import schema_field_description

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.relation_extract import RelationKind, RelationStance


CsvJsonFormat = Literal["json", "csv"]


class RelationGraphEvent(BaseModel):
    summary: str = Field(description=schema_field_description("summary"))
    volume_number: Optional[int] = Field(default=None, description=schema_field_description("volume_number"))
    chapter_number: Optional[int] = Field(default=None, description=schema_field_description("chapter_number"))


class RelationGraphKey(BaseModel):
    source: str = Field(description=schema_field_description("source"))
    target: str = Field(description=schema_field_description("target"))
    kind_en: str = Field(description=schema_field_description("kind_en"))


class RelationGraphInput(BaseModel):
    source: str = Field(description=schema_field_description("source"))
    target: str = Field(description=schema_field_description("target"))
    kind_en: Optional[str] = Field(default=None, description=schema_field_description("kind_en"))
    kind_cn: Optional[str] = Field(default=None, description=schema_field_description("kind_cn"))
    kind: Optional[str] = Field(default=None, description=schema_field_description("kind"))
    fact: Optional[str] = Field(default=None, description=schema_field_description("fact"))
    description: Optional[str] = Field(default=None, description=schema_field_description("description"))
    a_to_b_addressing: Optional[str] = Field(default=None, description=schema_field_description("a_to_b_addressing"))
    b_to_a_addressing: Optional[str] = Field(default=None, description=schema_field_description("b_to_a_addressing"))
    recent_dialogues: List[str] = Field(default_factory=list, description=schema_field_description("recent_dialogues"))
    recent_event_summaries: List[RelationGraphEvent] = Field(default_factory=list, description=schema_field_description("recent_event_summaries"))
    stance: Optional[RelationStance] = Field(default=None, description=schema_field_description("stance"))


class RelationGraphRecord(BaseModel):
    source: str
    target: str
    kind_en: str
    kind_cn: str
    kind: str
    fact: str
    a_to_b_addressing: Optional[str] = None
    b_to_a_addressing: Optional[str] = None
    recent_dialogues: List[str] = Field(default_factory=list)
    recent_event_summaries: List[RelationGraphEvent] = Field(default_factory=list)
    stance: Optional[RelationStance] = None
    updated_at: Optional[str] = None


class RelationGraphListRequest(BaseModel):
    project_id: int
    keyword: Optional[str] = None
    kinds: List[RelationKind] = Field(default_factory=list)
    stances: List[RelationStance] = Field(default_factory=list)
    offset: int = 0
    limit: int = 50


class RelationGraphListResponse(BaseModel):
    items: List[RelationGraphRecord] = Field(default_factory=list)
    total: int = 0


class RelationGraphUpsertRequest(BaseModel):
    project_id: int
    relation: RelationGraphInput


class RelationGraphDeleteRequest(BaseModel):
    project_id: int
    key: RelationGraphKey


class RelationGraphBatchDeleteRequest(BaseModel):
    project_id: int
    keys: List[RelationGraphKey] = Field(default_factory=list)


class RelationGraphBatchUpdateKindRequest(BaseModel):
    project_id: int
    keys: List[RelationGraphKey] = Field(default_factory=list)
    new_kind_en: Optional[str] = Field(default=None, description=schema_field_description("new_kind_en"))
    new_kind_cn: Optional[str] = Field(default=None, description=schema_field_description("new_kind_cn"))


class RelationGraphBatchUpdateStanceRequest(BaseModel):
    project_id: int
    keys: List[RelationGraphKey] = Field(default_factory=list)
    stance: Optional[RelationStance] = Field(default=None, description=schema_field_description("stance"))


class RelationGraphBatchAppendEventsRequest(BaseModel):
    project_id: int
    keys: List[RelationGraphKey] = Field(default_factory=list)
    events: List[RelationGraphEvent] = Field(default_factory=list)
    max_size: int = 20


class RelationGraphBatchCreateRequest(BaseModel):
    project_id: int
    relations: List[RelationGraphInput] = Field(default_factory=list)


class RelationGraphWriteResponse(BaseModel):
    affected: int = 0


class RelationGraphExportRequest(BaseModel):
    project_id: int
    format: CsvJsonFormat = "json"
    keys: List[RelationGraphKey] = Field(default_factory=list)


class RelationGraphExportResponse(BaseModel):
    filename: str
    mime_type: str
    content: str


class RelationGraphImportRequest(BaseModel):
    project_id: int
    format: CsvJsonFormat = "json"
    content: str


class RelationGraphImportResponse(BaseModel):
    created: int = 0
    updated: int = 0
    failed: int = 0
    errors: List[str] = Field(default_factory=list)


class RelationGraphKindOption(BaseModel):
    kind_cn: str
    kind_en: str


class RelationGraphMetaResponse(BaseModel):
    kinds: List[RelationGraphKindOption] = Field(default_factory=list)
    stances: List[RelationStance] = Field(default_factory=list)
