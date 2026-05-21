
from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field
from loguru import logger

from ...registry import register_node
from ..base import BaseNode
from app.services.ai.core.chat_model_factory import build_chat_model
from app.services.ai.core.agent_builder import build_agent
from app.services.ai.assistant.tools import (
    ASSISTANT_TOOL_REGISTRY,
    AssistantDeps,
    set_assistant_deps,
)


# ============================================================
# Input/Output Models
# ============================================================

class AgentInput(BaseModel):
    instruction: str = Field(..., description=schema_field_description("instruction"))
    project_id: Optional[int] = Field(None, description=schema_field_description("project_id"))
    system_prompt: Optional[str] = Field(
        "You are a professional writing assistant for novel creation tasks.",
        description=schema_field_description("system_prompt")
    )
    history: List[Dict[str, Any]] = Field(default_factory=list, description=schema_field_description("history"))
    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"), gt=0)
    temperature: float = Field(0.7, description=schema_field_description("temperature"), ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, description=schema_field_description("max_tokens"), gt=0)
    timeout: int = Field(60, description=schema_field_description("timeout"), gt=0)
    role_name: str = Field("Assistant", description=schema_field_description("role_name"))
    tools: List[str] = Field(
        default_factory=list,
        description=schema_field_description("tools"),
        json_schema_extra={"x-component": "ToolMultiSelect"}
    )
    max_steps: int = Field(10, ge=1, le=50, description=schema_field_description("max_steps"))


class AgentOutput(BaseModel):
    response: str = Field(..., description=schema_field_description("response"))
    new_history: List[Dict[str, Any]] = Field(..., description=schema_field_description("new_history"))
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description=schema_field_description("artifacts"))


# ============================================================
# Node Implementation
# ============================================================

class AgentNode(BaseNode[AgentInput, AgentOutput]):




    node_type = "AI.Agent"
    category = "ai"
    label = "AI Agent"
    description = "Tool-enabled writing assistant agent"

    input_model = AgentInput
    output_model = AgentOutput

    async def execute(self, input_data: AgentInput) -> AsyncIterator[AgentOutput]:

        project_id = input_data.project_id or -1

        deps = AssistantDeps(
            session=self.context.session,
            project_id=project_id
        )
        set_assistant_deps(deps)

        model = build_chat_model(
            session=self.context.session,
            llm_config_id=input_data.llm_config_id,
            temperature=input_data.temperature,
            max_tokens=input_data.max_tokens,
            timeout=input_data.timeout,
        )

        selected_tools = []
        for tool_name in input_data.tools:
            tool = ASSISTANT_TOOL_REGISTRY.get(tool_name)
            if tool:
                selected_tools.append(tool)
            else:


                pass
        pass
        if not selected_tools:


            pass
        agent = build_agent(
            model=model,
            tools=selected_tools,
            system_prompt=input_data.system_prompt,
            enable_summarization=False,
        )

        messages = []

        if input_data.history:
            messages.extend(input_data.history)

        messages.append({
            "role": "user",
            "content": input_data.instruction
        })

        result = await agent.ainvoke({"messages": messages})

        response_text = ""
        final_messages = []

        if isinstance(result, dict):
            result_messages = result.get("messages", [])
            if result_messages:
                for msg in reversed(result_messages):
                    if hasattr(msg, 'content'):
                        response_text = msg.content
                        break
                    elif isinstance(msg, dict) and msg.get("role") == "assistant":
                        response_text = msg.get("content", "")
                        break

                final_messages = result_messages

        serializable_history = []
        for msg in final_messages:
            if hasattr(msg, 'dict'):
                serializable_history.append(msg.dict())
            elif hasattr(msg, 'model_dump'):
                serializable_history.append(msg.model_dump())
            elif isinstance(msg, dict):
                serializable_history.append(msg)
            else:
                serializable_history.append({
                    "role": "assistant" if hasattr(msg, 'content') else "user",
                    "content": str(msg)
                })

        logger.info(
            f"[AI.Agent] Agent \u6267\u884c\u6210\u529f: role={input_data.role_name}, "
            f"tools={len(selected_tools)}, response_length={len(response_text)}"
        )

        yield AgentOutput(
            response=response_text,
            new_history=serializable_history,
            artifacts=[]
        )

