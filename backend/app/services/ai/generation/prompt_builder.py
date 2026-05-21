
import json
from typing import Dict, Any, Optional
from sqlmodel import Session

from app.services import prompt_service


FALLBACK_INSTRUCTION_GUIDE = """## Instruction Flow Generation Guide

Generate content by mixing brief natural-language reasoning with one JSON instruction per line.

## Available Instructions

1. **Set a field value**
   {"op":"set","path":"<path>","value":<value>}
   - Path must be a JSON Pointer starting with `/`.
   - Example: {"op":"set","path":"/name","value":"Example"}

2. **Append to an array**
   {"op":"append","path":"<array_path>","value":<item>}

3. **Finish generation**
   {"op":"done"}

## Rules
- Output each JSON instruction on its own line.
- Values must match the provided JSON Schema.
- Generate a few related fields at a time.
- After all required fields are complete, output {"op":"done"}.
"""


def build_instruction_system_prompt(
    session: Session,
    schema: Dict[str, Any],
    card_prompt: Optional[str] = None
) -> str:
    parts = []

    if card_prompt:
        parts.append(card_prompt)

    instruction_guide = FALLBACK_INSTRUCTION_GUIDE
    try:
        prompt = prompt_service.get_prompt_by_identifier(session, "instruction_flow_guide")
        if prompt and prompt.template:
            instruction_guide = prompt.template
    except Exception:
        pass
    parts.append(instruction_guide)

    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
    schema_section = f"\n## \u76ee\u6807\u6570\u636e\u7ed3\u6784（JSON Schema）\n\n```json\n{schema_json}\n```\n\n\u8bf7\u53c2\u7167\u6b64 Schema \u4f7f\u7528\u6307\u4ee4\u6d41\u9010\u6b65\u751f\u6210\u5185\u5bb9。"
    parts.append(schema_section)

    return "\n\n".join(parts)


def build_user_task_prompt(
    user_prompt: str,
    context_info: Optional[str] = None,
    current_data: Optional[Dict[str, Any]] = None
) -> str:
    parts = []

    if context_info:
        parts.append(f"## \u76f8\u5173\u4e0a\u4e0b\u6587\n\n{context_info}")

    if user_prompt:
        parts.append(f"## \u7528\u6237\u8981\u6c42\n\n{user_prompt}")
    else:
        parts.append("Please start generating card content.")

    if current_data:
        current_data_json = json.dumps(current_data, indent=2, ensure_ascii=False)
        parts.append(f"## \u5f53\u524d\u5df2\u751f\u6210\u7684\u6570\u636e\n\n```json\n{current_data_json}\n```\n\n\u8bf7\u7ee7\u7eed\u751f\u6210\u7f3a\u5931\u7684\u5b57\u6bb5。")

    return "\n\n".join(parts)
