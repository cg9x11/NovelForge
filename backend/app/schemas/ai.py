from app.locales import schema_field_description
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal


ContinuationWordControlMode = Literal["prompt_only", "balanced"]

class ContinuationRequest(BaseModel):
    previous_content: str = Field(default="", description=schema_field_description("previous_content"))
    llm_config_id: int
    stream: bool = False
    project_id: Optional[int] = None
    volume_number: Optional[int] = None
    chapter_number: Optional[int] = None
    participants: Optional[List[str]] = None
    temperature: Optional[float] = Field(default=None, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(default=None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(default=None, description=schema_field_description("timeout"))
    context_info: Optional[str] = Field(default=None, description=schema_field_description("context_info"))
    existing_word_count: Optional[int] = Field(default=None, description=schema_field_description("existing_word_count"))
    target_word_count: Optional[int] = Field(default=None, description=schema_field_description("target_word_count"))
    word_control_mode: Optional[ContinuationWordControlMode] = Field(
        default=None,
        description=schema_field_description("word_control_mode"),
    )
    continuation_guidance: Optional[str] = Field(default=None, description=schema_field_description("continuation_guidance"))
    budget_round_hint: Optional[int] = Field(default=None, description=schema_field_description("budget_round_hint"))
    remaining_word_count_hint: Optional[int] = Field(default=None, description=schema_field_description("remaining_word_count_hint"))
    is_final_round_hint: Optional[bool] = Field(default=None, description=schema_field_description("is_final_round_hint"))
    prompt_name: Optional[str] = Field(default=None, description=schema_field_description("prompt_name"))
    append_continuous_novel_directive: bool = Field(default=True, description=schema_field_description("append_continuous_novel_directive"))

class ContinuationResponse(BaseModel):
    content: str


class AssistantChatRequest(BaseModel):
    context_info: str = Field(description=schema_field_description("context_info"))
    user_prompt: str = Field(default="", description=schema_field_description("user_prompt"))

    project_id: int = Field(description=schema_field_description("project_id"))
    llm_config_id: int = Field(description=schema_field_description("llm_config_id"))
    prompt_name: str = Field(default="idea_chat", description=schema_field_description("prompt_name"))

    temperature: Optional[float] = Field(default=None, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(default=None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(default=None, description=schema_field_description("timeout"))
    stream: bool = Field(default=True, description=schema_field_description("stream"))
    thinking_enabled: Optional[bool] = Field(default=None, description=schema_field_description("thinking_enabled"))
    context_summarization_enabled: Optional[bool] = Field(default=None, description=schema_field_description("context_summarization_enabled"))
    context_summarization_threshold: Optional[int] = Field(default=None, description=schema_field_description("context_summarization_threshold"))
    react_mode_enabled: Optional[bool] = Field(default=None, description=schema_field_description("react_mode_enabled"))


class GeneralAIRequest(BaseModel):
    input: Dict[str, Any]
    llm_config_id: Optional[int] = None
    prompt_name: Optional[str] = None
    response_model_name: Optional[Dict[str, Any]] | Optional[str] = None
    response_model_schema: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = Field(default=None, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(default=None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(default=None, description=schema_field_description("timeout"))
    deps: Optional[str] = Field(default=None, description=schema_field_description("deps"))
    exclude_ai_fields: Optional[bool] = Field(default=True, description=schema_field_description("exclude_ai_fields"))

    class Config:
        extra = 'ignore'
