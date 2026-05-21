from __future__ import annotations
from app.locales import schema_field_description

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowAgentMode(str, Enum):
    SUGGEST = "suggest"
    AUTO_APPLY = "auto_apply"


class WorkflowAgentChatRequest(BaseModel):
    workflow_id: int = Field(description=schema_field_description("workflow_id"))
    llm_config_id: int = Field(description=schema_field_description("llm_config_id"))
    user_prompt: str = Field(default="", description=schema_field_description("user_prompt"))
    mode: WorkflowAgentMode = Field(default=WorkflowAgentMode.SUGGEST, description=schema_field_description("mode"))
    conversation_id: Optional[str] = Field(default=None, description=schema_field_description("conversation_id"))

    temperature: Optional[float] = Field(default=None, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(default=None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(default=None, description=schema_field_description("timeout"))
    thinking_enabled: Optional[bool] = Field(default=None, description=schema_field_description("thinking_enabled"))
    react_mode_enabled: Optional[bool] = Field(default=None, description=schema_field_description("react_mode_enabled"))
    history_messages: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description=schema_field_description("history_messages"),
    )
    pending_code: Optional[str] = Field(
        default=None,
        description=schema_field_description("pending_code"),
    )


class WorkflowPatchOp(BaseModel):
    op: str = Field(description=schema_field_description("op"))
    target_node: Optional[str] = Field(default=None, description=schema_field_description("target_node"))
    new_code: Optional[str] = Field(default=None, description=schema_field_description("new_code"))
    new_block: Optional[str] = Field(default=None, description=schema_field_description("new_block"))
    new_meta: Optional[Dict[str, Any]] = Field(default=None, description=schema_field_description("new_meta"))
    new_call: Optional[str] = Field(default=None, description=schema_field_description("new_call"))
    old_name: Optional[str] = Field(default=None, description=schema_field_description("old_name"))
    new_name: Optional[str] = Field(default=None, description=schema_field_description("new_name"))
    reason: Optional[str] = Field(default=None, description=schema_field_description("reason"))


class WorkflowPatchRequest(BaseModel):
    base_revision: str = Field(description=schema_field_description("base_revision"))
    patch_ops: List[WorkflowPatchOp] = Field(default_factory=list, description=schema_field_description("patch_ops"))
    dry_run: bool = Field(default=False, description=schema_field_description("dry_run"))


class WorkflowPatchResponse(BaseModel):
    success: bool
    workflow_id: int
    base_revision: str
    new_revision: Optional[str] = None
    applied_ops: int = 0
    changed_nodes: List[str] = Field(default_factory=list)
    diff: str = ""
    new_code: str = ""
    parse_result: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
