
from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field



class InstructionBase(BaseModel):
    op: str = Field(..., description=schema_field_description("op"))


class SetInstruction(InstructionBase):
    op: Literal["set"] = "set"
    path: str = Field(..., description=schema_field_description("path"))
    value: Any = Field(..., description=schema_field_description("value"))


class AppendInstruction(InstructionBase):
    op: Literal["append"] = "append"
    path: str = Field(..., description=schema_field_description("path"))
    value: Any = Field(..., description=schema_field_description("value"))


class DoneInstruction(InstructionBase):
    op: Literal["done"] = "done"


Instruction = SetInstruction | AppendInstruction | DoneInstruction



class GenerationConfig(BaseModel):
    mode: Literal["instruction_stream"] = Field(
        default="instruction_stream",
        description=schema_field_description("mode")
    )
    prompt_template: Optional[str] = Field(
        default=None,
        description=schema_field_description("prompt_template")
    )
    field_hints: Optional[Dict[str, str]] = Field(
        default=None,
        description=schema_field_description("field_hints")
    )
    field_order: Optional[List[str]] = Field(
        default=None,
        description=schema_field_description("field_order")
    )
    custom: Optional[Dict[str, Any]] = Field(
        default=None,
        description=schema_field_description("custom")
    )



class ConversationMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(..., description=schema_field_description("role"))
    content: str = Field(..., description=schema_field_description("content"))


class InstructionGenerateRequest(BaseModel):


    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"))

    user_prompt: str = Field(default="", description=schema_field_description("user_prompt"))

    response_model_schema: Dict[str, Any] = Field(..., description=schema_field_description("response_model_schema"))

    current_data: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("current_data"))

    conversation_context: List[ConversationMessage] = Field(
        default_factory=list,
        description=schema_field_description("conversation_context")
    )

    generation_config: Optional[GenerationConfig] = Field(
        default=None,
        description=schema_field_description("generation_config")
    )

    prompt_template: Optional[str] = Field(
        default=None,
        description=schema_field_description("prompt_template")
    )

    context_info: Optional[str] = Field(
        default=None,
        description=schema_field_description("context_info")
    )

    temperature: Optional[float] = Field(default=0.7, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(default=None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(default=150, description=schema_field_description("timeout"))

    deps: Optional[str] = Field(default=None, description=schema_field_description("deps"))



class ThinkingEvent(BaseModel):
    type: Literal["thinking"] = "thinking"
    text: str = Field(..., description=schema_field_description("text"))


class InstructionEvent(BaseModel):
    type: Literal["instruction"] = "instruction"
    instruction: Instruction = Field(..., description=schema_field_description("instruction"))


class WarningEvent(BaseModel):
    type: Literal["warning"] = "warning"
    text: str = Field(..., description=schema_field_description("text"))


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    text: str = Field(..., description=schema_field_description("text"))


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    success: bool = Field(default=True, description=schema_field_description("success"))
    message: Optional[str] = Field(default=None, description=schema_field_description("message"))


StreamEvent = ThinkingEvent | InstructionEvent | WarningEvent | ErrorEvent | DoneEvent
