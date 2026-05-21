
import json
import re
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional
from sqlmodel import Session
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from pydantic import ValidationError
from loguru import logger

from app.services.ai.core.chat_model_factory import build_chat_model
from app.services.ai.core.quota_manager import precheck_quota, record_usage
from app.services.ai.core.token_utils import estimate_tokens
from app.services.ai.core.model_builder import build_model_from_json_schema
from app.services.ai.generation.instruction_validator import (
    validate_instruction,
    apply_instruction,
    format_validation_errors
)
from app.services.ai.generation.prompt_builder import build_user_task_prompt
from app.schemas.instruction import ConversationMessage


def _format_provider_error(error: Exception) -> str:
    parts = [f"{type(error).__name__}: {error}"]
    for attr in ("status_code", "code", "type", "param", "request_id"):
        value = getattr(error, attr, None)
        if value:
            parts.append(f"{attr}={value}")
    response = getattr(error, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", None)
        if status_code:
            parts.append(f"response_status={status_code}")
        try:
            request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
            if request_id:
                parts.append(f"response_request_id={request_id}")
        except Exception:
            pass
        try:
            body = response.json()
        except Exception:
            body = getattr(response, "text", None)
        if body:
            parts.append(f"response_body={body}")
    body = getattr(error, "body", None)
    if body:
        parts.append(f"error_body={body}")
    return " | ".join(parts)


def _estimate_messages_input_tokens(messages: List[BaseMessage]) -> int:
    parts: List[str] = []
    for msg in messages:
        content = getattr(msg, "content", None)
        if isinstance(content, str):
            parts.append(content)
            continue
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str) and text:
                        parts.append(text)
                elif isinstance(block, str):
                    parts.append(block)
    return estimate_tokens("\n".join(parts))


async def generate_instruction_stream(
    session: Session,
    llm_config_id: int,
    user_prompt: str,
    system_prompt: str,
    schema: Dict[str, Any],
    current_data: Dict[str, Any],
    conversation_context: List[ConversationMessage],
    context_info: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    timeout: float = 150,
    max_retry: int = 3,
    track_stats: bool = True,
) -> AsyncIterator[Dict[str, Any]]:
    try:
        chat_model = build_chat_model(
            session=session,
            llm_config_id=llm_config_id,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
    except Exception as e:
        yield {
            "type": "error",
            "text": f"Failed to initialize LLM: {str(e)}"
        }
        return

    try:
        DynamicModel = build_model_from_json_schema('DynamicResponseModel', schema)
    except Exception as e:
        yield {
            "type": "error",
            "text": f"Failed to parse schema: {str(e)}"
        }
        return

    collected_data = dict(current_data)

    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]

    if not conversation_context:
        task_prompt = build_user_task_prompt(
            user_prompt=user_prompt or "Please start generating card content",
            context_info=context_info,
            current_data=collected_data if collected_data else None
        )
        messages.append(HumanMessage(content=task_prompt))
    else:
        for msg in conversation_context:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        if collected_data:
            current_data_info = f"\n\n## Current generated data\n\n```json\n{json.dumps(collected_data, ensure_ascii=False, indent=2)}\n```\n\nContinue generating missing fields. Do not regenerate existing fields."

            if messages and isinstance(messages[-1], HumanMessage):
                messages[-1].content += current_data_info
            else:
                messages.append(HumanMessage(content=current_data_info))

    # logger.info("=" * 80)
    # for idx, msg in enumerate(messages):
    #     msg_type = type(msg).__name__
    #     content_preview = msg.content
    #     logger.info(f"  [{idx}] {msg_type}: {content_preview}")
    # logger.info("=" * 80)

    failed_instructions = []  # Accumulated failed instructions
    generation_completed = False  # Marks normal completion

    for attempt in range(max_retry):
        attempt_input_tokens = _estimate_messages_input_tokens(messages)
        if track_stats:
            ok, reason = precheck_quota(
                session,
                llm_config_id,
                attempt_input_tokens,
                need_calls=1,
            )
            if not ok:
                yield {
                    "type": "error",
                    "text": f"LLM quota insufficient: {reason}",
                }
                return

        attempt_output_text = ""
        attempt_started = False
        attempt_aborted = False
        try:
            buffer = ""
            ai_output_lines = []  # Record all AI output for feedback
            need_fix = False  # Whether fix is needed after completeness validation failure
            fix_prompt = ""  # Fix prompt
            should_break_stream = False  # Whether stream should break

            json_buffer = ""  # JSON accumulation buffer
            brace_depth = 0  # Brace depth
            in_string = False  # Whether inside string
            escape_next = False  # Whether next character is escaped

            attempt_started = True
            async for chunk in chat_model.astream(messages):
                raw = getattr(chunk, "content", "")
                if isinstance(raw, str):
                    content = raw
                elif isinstance(raw, list):
                    parts = []
                    for part in raw:
                        if isinstance(part, dict):
                            if part.get("type") == "text" and isinstance(part.get("text"), str):
                                parts.append(part["text"])
                        elif isinstance(part, str):
                            parts.append(part)
                    content = "".join(parts)
                else:
                    content = str(raw) if raw is not None else ""

                if not content:
                    continue

                attempt_output_text += content
                buffer += content

                lines = buffer.split('\n')
                buffer = lines[-1]  # Keep incomplete line

                for line in lines[:-1]:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    ai_output_lines.append(line_stripped)  # Record output

                    instruction = None
                    for char in line:
                        if escape_next:
                            if brace_depth > 0:
                                json_buffer += char
                            escape_next = False
                            continue

                        if char == '\\':
                            if brace_depth > 0:
                                json_buffer += char
                            escape_next = True
                            continue

                        if char == '"' and brace_depth > 0:
                            in_string = not in_string
                            json_buffer += char
                            continue

                        if not in_string:
                            if char == '{':
                                brace_depth += 1
                                json_buffer += char
                            elif char == '}':
                                json_buffer += char
                                brace_depth -= 1

                                if brace_depth == 0:
                                    instruction = try_parse_instruction(json_buffer)
                                    if not instruction:
                                        try:
                                            cleaned_json = json_buffer.replace(",}", "}").replace(",]", "]")
                                            instruction = try_parse_instruction(cleaned_json)
                                        except Exception:
                                            pass

                                        if not instruction:
                                            failed_instructions.append({
                                                "instruction": json_buffer[:100],
                                                "error": "JSON parse failed"
                                            })
                                            yield {
                                                "type": "warning",
                                                "text": f"Cannot parse instruction JSON: {json_buffer[:50]}..."
                                            }
                                            if len(failed_instructions) >= 5:
                                                should_break_stream = True

                                    json_buffer = ""
                                    if instruction:
                                        break  # Instruction found; process it
                            elif brace_depth > 0:
                                json_buffer += char
                        elif brace_depth > 0:
                            json_buffer += char

                    if instruction:
                        # ... (existing instruction processing logic) ...
                        try:
                            # ...
                            validate_instruction(instruction, schema)
                            apply_instruction(collected_data, instruction)
                            yield {
                                "type": "instruction",
                                "instruction": instruction
                            }

                            # done logic ...
                            if instruction.get('op') == 'done':




                                has_instruction_errors = len(failed_instructions) > 0

                                validation_errors = []
                                try:
                                    validated_model = DynamicModel(**collected_data)
                                except ValidationError as e:
                                    validation_errors = e.errors()

                                if has_instruction_errors or validation_errors:




                                    feedback_parts = []

                                    if failed_instructions:
                                        feedback_parts.append("[Instruction execution failed] These instructions failed to parse or execute:")
                                        for item in failed_instructions:
                                            feedback_parts.append(f"- {item['error']}: {str(item['instruction'])[:100]}")

                                    if validation_errors:
                                        feedback_parts.append("\n[Data completeness missing] These fields failed validation:")
                                        feedback_parts.append(format_validation_errors(validation_errors))

                                    feedback_text = "\n".join(feedback_parts)

                                    need_fix = True
                                    fix_prompt = f"""You sent a done instruction, but generation has errors or incomplete data:

{feedback_text}

Current successfully applied data state:
```json
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
```

Fix the instruction errors above and fill missing required fields.
"""
                                    should_break_stream = True
                                else:
                                    generation_completed = True
                                    yield {
                                        "type": "done",
                                        "success": True,
                                        "message": "Generation complete",
                                        "final_data": validated_model.model_dump(mode='json')
                                    }
                                    return

                        except ValueError as e:
                            failed_instructions.append({"instruction": instruction, "error": str(e)})
                            yield {"type": "warning", "text": f"Instruction validation failed: {str(e)}"}
                            # should_break_stream = True

                    else:
                        if brace_depth == 0 and line_stripped:
                             yield {
                                "type": "thinking",
                                "text": line
                            }

                if should_break_stream:
                    break

            if json_buffer.strip() and brace_depth == 0:
                instruction = try_parse_instruction(json_buffer.strip())
                if instruction:
                    try:
                        validate_instruction(instruction, schema)
                        apply_instruction(collected_data, instruction)
                        yield {
                            "type": "instruction",
                            "instruction": instruction
                        }
                    except ValueError as e:


                        pass
            pass
            if buffer.strip():
                instruction = try_parse_instruction(buffer.strip())
                if instruction:
                    try:
                        validate_instruction(instruction, schema)
                        apply_instruction(collected_data, instruction)
                        yield {
                            "type": "instruction",
                            "instruction": instruction
                        }

                        if instruction.get('op') == 'done':
                            try:
                                validated_model = DynamicModel(**collected_data)
                                yield {
                                    "type": "done",
                                    "success": True,
                                    "message": "Generation complete",
                                    "final_data": validated_model.model_dump(mode='json')
                                }
                                return
                            except ValidationError as e:
                                error_msg = format_validation_errors(e.errors())
                                need_fix = True
                                fix_prompt = f"""Generated data is incomplete or invalid. Fix these issues:

{error_msg}

Current data:
```json
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
```

Continue generating missing or invalid fields. Output {"op":"done"} again when complete.
"""
                                should_break_stream = True
                    except ValueError as e:
                        pass
                else:
                    yield {
                        "type": "thinking",
                        "text": buffer.strip()
                    }


            if need_fix:




                messages.append(AIMessage(content="\n".join(ai_output_lines)))
                messages.append(HumanMessage(content=fix_prompt))

                if attempt < max_retry - 1:
                    retry_delay = min(2 ** attempt, 5)  # Exponential backoff: 1s, 2s, 4s...
                    await asyncio.sleep(retry_delay)

                continue

            if failed_instructions:
                error_summary = "\n".join([
                    f"- Instruction: {json.dumps(item['instruction'], ensure_ascii=False)}\n  Error: {item['error']}"
                    for item in failed_instructions
                ])

                feedback_prompt = f"""
The following {len(failed_instructions)} generated instructions failed validation:

{error_summary}

Current successfully applied data:
```json
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
```

Notes:
1. Check whether field paths are correct
2. For array fields, ensure field is an array before append
3. For object fields, use set for the whole object or nested paths for child fields
4. Refer to schema and ensure operators match field types

Fix these errors and continue generation. Output {"op":"done"} when complete.
"""


                messages.append(AIMessage(content="\n".join(ai_output_lines)))
                messages.append(HumanMessage(content=feedback_prompt))

                failed_instructions = []

                if attempt < max_retry - 1:
                    retry_delay = min(2 ** attempt, 5)  # Exponential backoff: 1s, 2s, 4s...
                    await asyncio.sleep(retry_delay)

                continue


            try:
                validated_model = DynamicModel(**collected_data)

                yield {
                    "type": "done",
                    "success": True,
                    "message": "Generation ended (auto-completed)",
                    "final_data": validated_model.model_dump(mode='json')
                }
                generation_completed = True
                break
            except Exception as e:
                 pass

            try:
                validated_model = DynamicModel(**collected_data)

                schema_properties = schema.get("properties", {})
                missing_optional_fields = []
                for field_name, field_schema in schema_properties.items():
                    is_optional = field_name not in schema.get("required", [])
                    if is_optional:
                        field_value = collected_data.get(field_name)
                        if field_value is None or field_value == [] or field_value == "":
                            missing_optional_fields.append(field_name)

                if missing_optional_fields:
                    yield {
                        "type": "warning",
                        "text": f"Warning: generation was truncated (LLM did not send done). Missing fields: {', '.join(missing_optional_fields)}.\n\nPossible reasons:\n1. max_tokens is too small (increase recommended)\n2. Network instability or service rate limit\n\nSuggestion: retry later or adjust parameters."
                    }
                    if attempt < max_retry - 1:
                        fix_prompt = f"""
Generation incomplete. Missing fields: {', '.join(missing_optional_fields)}

Current data:
```json
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
```

Continue generating missing fields. Output {"op":"done"} when complete.
"""
                        messages.append(AIMessage(content="\n".join(ai_output_lines)))
                        messages.append(HumanMessage(content=fix_prompt))

                        retry_delay = min(2 ** attempt, 5)
                        await asyncio.sleep(retry_delay)

                        continue
                    else:
                        generation_completed = True
                        yield {
                            "type": "done",
                            "success": True,
                            "message": f"Generation complete (some fields missing: {', '.join(missing_optional_fields)})"
                        }
                        return

                generation_completed = True
                yield {
                    "type": "done",
                    "success": True,
                    "message": "Generation complete (LLM did not send done, but data is complete)"
                }
                return
            except ValidationError as e:
                error_msg = format_validation_errors(e.errors())

                if attempt == 0:
                    yield {
                        "type": "error",
                        "text": f"Warning: generation was truncated. Possible reasons:\n1. max_tokens is too small (increase recommended)\n2. Network instability or service rate limit\n\nSuggestion: retry later or adjust parameters."
                    }
                    break

                need_fix = True
                fix_prompt = f"""
Generation interrupted; data incomplete. Missing or invalid fields:

{error_msg}

Current data:
```json
{json.dumps(collected_data, ensure_ascii=False, indent=2)}
```

Continue generating missing fields. Output {"op":"done"} when complete.
"""
                messages.append(AIMessage(content="\n".join(ai_output_lines)))
                messages.append(HumanMessage(content=fix_prompt))

                if attempt < max_retry - 1:
                    retry_delay = min(2 ** attempt, 4)
                    await asyncio.sleep(retry_delay)

                continue

        except asyncio.CancelledError:
            attempt_aborted = True
            raise
        except Exception as e:
            logger.exception(
                "[InstructionGeneration] LLM stream failed "
                f"attempt={attempt + 1}/{max_retry} "
                f"llm_config_id={llm_config_id} "
                f"error={_format_provider_error(e)}"
            )
            yield {
                "type": "error",
                "text": f"Generation failed: {_format_provider_error(e)}"
            }
            return
        finally:
            if attempt_started and track_stats:
                try:
                    record_usage(
                        session,
                        llm_config_id,
                        attempt_input_tokens,
                        estimate_tokens(attempt_output_text),
                        calls=1,
                        aborted=attempt_aborted,
                    )
                except Exception as usage_error:


                    pass
    if not generation_completed:
        logger.error(
            "[InstructionGeneration] reached max retry count "
            f"max_retry={max_retry} "
            f"llm_config_id={llm_config_id} "
            f"collected_fields={list(collected_data.keys())}"
        )
        yield {
            "type": "error",
            "text": f"Generation failed: reached max retry count {max_retry}"
        }


def try_parse_instruction(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if line.startswith('```') or line.endswith('```'):
        return None

    try:
        obj = json.loads(line)
        if isinstance(obj, dict) and 'op' in obj:
            return obj
    except json.JSONDecodeError:
        pass

    start_idx = line.find('{')
    if start_idx == -1:
        return None

    brace_count = 0
    in_string = False
    escape_next = False

    for i in range(start_idx, len(line)):
        char = line[i]

        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1

                if brace_count == 0:
                    json_str = line[start_idx:i+1]
                    try:
                        obj = json.loads(json_str)
                        if isinstance(obj, dict) and 'op' in obj:
                            return obj
                    except json.JSONDecodeError:
                        next_start = line.find('{', i+1)
                        if next_start != -1:
                            start_idx = next_start
                            brace_count = 0
                            in_string = False
                            escape_next = False
                        else:
                            return None

    return None
