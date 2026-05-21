
from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator, TYPE_CHECKING
from pydantic import BaseModel, Field
from loguru import logger

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from ...registry import register_node
from ..base import BaseNode
from app.services.ai.core.llm_service import generate_structured


# ============================================================
# Helper Models
# ============================================================

class DebateMessage(BaseModel):
    thought: str = Field(..., description=schema_field_description("thought"))
    content: str = Field(..., description=schema_field_description("content"))


# ============================================================
# Input/Output Models
# ============================================================

class DebateInput(BaseModel):
    topic: str = Field(..., description=schema_field_description("topic"))
    context: Optional[str] = Field(None, description=schema_field_description("context"))
    max_rounds: int = Field(3, description=schema_field_description("max_rounds"), ge=1, le=20)

    agent_1_name: str = Field("Pro", description=schema_field_description("agent_1_name"))
    agent_1_system_prompt: str = Field("", description=schema_field_description("agent_1_system_prompt"), json_schema_extra={"x-component": "Textarea"})
    agent_1_llm_config: int = Field(..., description=schema_field_description("agent_1_llm_config"), json_schema_extra={"x-component": "LLMSelect"})

    agent_2_name: str = Field("Con", description=schema_field_description("agent_2_name"))
    agent_2_system_prompt: str = Field("", description=schema_field_description("agent_2_system_prompt"), json_schema_extra={"x-component": "Textarea"})
    agent_2_llm_config: int = Field(..., description=schema_field_description("agent_2_llm_config"), json_schema_extra={"x-component": "LLMSelect"})

    temperature: float = Field(0.7, description=schema_field_description("temperature"), ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description=schema_field_description("max_tokens"))


class DebateOutput(BaseModel):
    summary: str = Field(..., description=schema_field_description("summary"))
    history: List[Dict[str, Any]] = Field(..., description=schema_field_description("history"))
    full_log: List[Dict[str, Any]] = Field(..., description=schema_field_description("full_log"))
    total_rounds: int = Field(..., description=schema_field_description("total_rounds"))


# ============================================================
# Node Implementation
# ============================================================

@register_node
class DebateNode(BaseNode[DebateInput, DebateOutput]):




    node_type = "AI.Debate"
    category = "ai"
    label = "AI Debate"
    description = "Run a multi-agent debate on a topic"

    input_model = DebateInput
    output_model = DebateOutput

    async def execute(self, input_data: DebateInput) -> AsyncIterator:
        from ...engine.async_executor import ProgressEvent

        checkpoint = getattr(self.context, 'checkpoint', None)
        completed_rounds = checkpoint.get('completed_rounds', 0) if checkpoint else 0
        history_public = checkpoint.get('history_public', []) if checkpoint else []
        full_log = checkpoint.get('full_log', []) if checkpoint else []

        agent_1_context = checkpoint.get('agent_1_context', []) if checkpoint else []
        agent_2_context = checkpoint.get('agent_2_context', []) if checkpoint else []

        if completed_rounds == 0:
            user_input = f"\u8fa9\u8bba\u4e3b\u9898：{input_data.topic}"
            if input_data.context:
                user_input += f"\n\n\u80cc\u666f\u8d44\u6599：\n{input_data.context}"


            agent_1_context = [user_input]
            agent_2_context = [user_input]
        else:


            pass
        pass
        for round_idx in range(completed_rounds, input_data.max_rounds):
            try:




                msg_1 = await self._agent_turn(
                    name=input_data.agent_1_name,
                    llm_config_id=input_data.agent_1_llm_config,
                    system_prompt=input_data.agent_1_system_prompt,
                    context=agent_1_context,
                    input_data=input_data,
                    role="Agent 1"
                )

                content_1 = msg_1.content
                thought_1 = msg_1.thought

                log_entry_1 = {
                    "round": round_idx + 1,
                    "role": input_data.agent_1_name,
                    "type": "Agent 1",
                    "thought": thought_1,
                    "content": content_1
                }
                full_log.append(log_entry_1)
                history_public.append({"role": input_data.agent_1_name, "content": content_1})

                agent_2_context.append(f"【{input_data.agent_1_name}】: {content_1}")
                agent_1_context.append(f"【\u6211\u7684\u53d1\u8a00】: {content_1}")


                msg_2 = await self._agent_turn(
                    name=input_data.agent_2_name,
                    llm_config_id=input_data.agent_2_llm_config,
                    system_prompt=input_data.agent_2_system_prompt,
                    context=agent_2_context,
                    input_data=input_data,
                    role="Agent 2"
                )

                content_2 = msg_2.content
                thought_2 = msg_2.thought

                log_entry_2 = {
                    "round": round_idx + 1,
                    "role": input_data.agent_2_name,
                    "type": "Agent 2",
                    "thought": thought_2,
                    "content": content_2
                }
                full_log.append(log_entry_2)
                history_public.append({"role": input_data.agent_2_name, "content": content_2})

                agent_2_context.append(f"【\u6211\u7684\u53d1\u8a00】: {content_2}")
                agent_1_context.append(f"【{input_data.agent_2_name}】: {content_2}")

                completed_rounds = round_idx + 1
                progress_percent = (completed_rounds / input_data.max_rounds) * 100


                yield ProgressEvent(
                    percent=progress_percent,
                    message=f"\u7b2c {completed_rounds}/{input_data.max_rounds} \u8f6e\u8fa9\u8bba\u5b8c\u6210",
                    data={
                        'completed_rounds': completed_rounds,
                        'history_public': history_public,
                        'full_log': full_log,
                        'agent_1_context': agent_1_context,
                        'agent_2_context': agent_2_context
                    }
                )

            except Exception as e:
                break


        yield DebateOutput(
            summary=history_public[-1]["content"] if history_public else "Debate incomplete",
            history=history_public,
            full_log=full_log,
            total_rounds=completed_rounds
        )

    async def _agent_turn(
        self,
        name: str,
        llm_config_id: int,
        system_prompt: str,
        context: List[str],
        input_data: DebateInput,
        role: str
    ) -> DebateMessage:
        try:
            user_prompt = "\n\n".join(context)

            response = await generate_structured(
                session=self.context.session,
                llm_config_id=llm_config_id,
                user_prompt=user_prompt,
                output_type=DebateMessage,
                system_prompt=system_prompt,
                temperature=input_data.temperature,
                max_tokens=input_data.max_tokens,
                max_retries=3
            )

            return response

        except Exception as e:
            raise

