import json
import uuid
from typing import Dict, Any, List, Optional
from contextvars import ContextVar

from loguru import logger
from langchain_core.tools import tool
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import select

from app.services.card_service import CardService
from app.db.models import Card
from app.services.card_type_service_utils import get_card_type_by_identifier
from app.services.ai.generation.instruction_validator import InstructionExecutor
from app.services.ai.card_type_schema import get_card_type_schema_payload
from app.schemas.tool_result import (
    ToolResult,
    ToolResultStatus,
    ConfirmationRequest,
    CardOperationResult,
    to_dict
)
import copy

REVIEW_RESULT_CARD_TYPE_NAME = "review_result_card"


class AssistantDeps:


    def __init__(self, session, project_id: int):
        self.session = session
        self.project_id = project_id


_assistant_deps_var: ContextVar[AssistantDeps | None] = ContextVar(
    "assistant_deps", default=None
)


def set_assistant_deps(deps: AssistantDeps) -> None:


    _assistant_deps_var.set(deps)


def _get_deps() -> AssistantDeps:


    deps = _assistant_deps_var.get()
    if deps is None:
        raise RuntimeError(
            "AssistantDeps not set. Call set_assistant_deps(...) before using tools."
        )
    return deps


def _get_card_type_schema(session, card_type_name: str) -> Dict[str, Any]:
    result = get_card_type_schema_payload(
        session,
        card_type_name,
        allow_model_name=False,
        require_schema=True,
    )
    if not result.get("success"):
        error = result.get("error")
        if error == "not_found":
            raise ValueError(f"Card type {card_type_name!r} does not exist")
        if error == "schema_not_defined":
            raise ValueError(f"Card type {card_type_name!r} has no Schema defined")
        raise ValueError("Failed to get card type schema")
    return result.get("schema") or {}


def _create_empty_card(session, card_type_name: str, title: str, parent_card_id: Optional[int], project_id: int) -> Card:
    card_type = get_card_type_by_identifier(session, card_type_name)
    if not card_type:
        raise ValueError(f"Card type {card_type_name!r} does not exist")

    card = Card(
        card_type_id=card_type.id,
        project_id=project_id,
        title=title,
        parent_id=parent_card_id,
        content={}
    )
    session.add(card)
    session.flush()  # get card.id

    return card


def _get_card_by_id(session, card_id: int, project_id: int) -> Optional[Card]:
    card = session.get(Card, card_id)
    if card and card.project_id == project_id:
        return card
    return None


@tool
def search_cards(
    card_type: Optional[str] = None,
    title_keyword: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Assistant tool: search_cards."""

    deps = _get_deps()

    logger.info(f" [Assistant.search_cards] card_type={card_type}, keyword={title_keyword}")

    query = deps.session.query(Card).filter(Card.project_id == deps.project_id)

    if card_type:
        resolved_card_type = get_card_type_by_identifier(deps.session, card_type)
        if not resolved_card_type:
            return {"success": True, "cards": [], "count": 0}
        query = query.filter(Card.card_type_id == resolved_card_type.id)

    if title_keyword:
        query = query.filter(Card.title.ilike(f'%{title_keyword}%'))

    cards = query.limit(limit).all()

    result = {
        "success": True,
        "cards": [
            {
                "id": c.id,
                "title": c.title,
                "type": c.card_type.name if c.card_type else "Unknown"
            }
            for c in cards
        ],
        "count": len(cards)
    }

    return result


@tool
def create_card(
    card_type: str,
    title: str,
    instructions: List[Dict[str, Any]],
    parent_card_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Assistant tool: create_card."""
    deps = _get_deps()

    logger.info(f"📝 [Assistant.create_card] type={card_type}, title={title}, instructions={len(instructions)}")

    try:
        schema = _get_card_type_schema(deps.session, card_type)

        card = _create_empty_card(
            session=deps.session,
            card_type_name=card_type,
            title=title,
            parent_card_id=parent_card_id,
            project_id=deps.project_id
        )


        executor = InstructionExecutor(schema=schema, initial_data={})

        result = executor.execute_batch(instructions)

        card.content = result["data"]
        flag_modified(card, "content")
        card.ai_modified = True
        card.needs_confirmation = True
        card.last_modified_by = "ai"
        deps.session.commit()


        if result["success"]:
            return {
                "success": True,
                "card_id": card.id,
                "card_title": title,
                "card_type": card_type,
                "message": f"Card {title!r} created successfully; filled {result['applied']} fields. Review content in frontend and save to trigger workflow.",
                "applied": result['applied'],
                "needs_confirmation": True
            }
        else:
            missing_fields_str = ", ".join(result["missing_fields"])
            return {
                "success": False,
                "card_id": card.id,
                "card_title": title,
                "card_type": card_type,
                "message": "Card was created but content is incomplete. Fill missing fields, then save in frontend to trigger workflow.",
                "error": f"Missing required fields: {missing_fields_str}",
                "missing_fields": result["missing_fields"],
                "current_data": result["data"],
                "applied": result["applied"],
                "failed": result["failed"],
                "failed_instructions": result.get("errors", []),
                "needs_confirmation": True
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Create failed: {str(e)}"
        }


def _update_card_impl(
    card_id: int,
    instructions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    deps = _get_deps()

    logger.info(f"📝 [_update_card_impl] card_id={card_id}, instructions={len(instructions)}")

    try:
        card = _get_card_by_id(deps.session, card_id, deps.project_id)
        if not card:
            return {
                "success": False,
                "error": f"Card ID={card_id} does not exist or does not belong to current project"
            }

        schema = _get_card_type_schema(deps.session, card.card_type.name)

        initial_data = copy.deepcopy(card.content) if isinstance(card.content, dict) else {}
        executor = InstructionExecutor(
            schema=schema,
            initial_data=initial_data
        )

        result = executor.execute_batch(instructions)

        card.content = result["data"]
        flag_modified(card, "content")
        card.ai_modified = True
        card.needs_confirmation = True
        card.last_modified_by = "ai"
        deps.session.commit()


        if result["success"]:
            return {
                "success": True,
                "card_id": card_id,
                "card_title": card.title,
                "message": f"Card {card.title!r} updated successfully; changed {result['applied']} fields. Review content in frontend and save to trigger workflow.",
                "current_data": result["data"],
                "applied": result["applied"],
                "needs_confirmation": True
            }
        else:
            missing_fields_str = ", ".join(result["missing_fields"])
            return {
                "success": True,
                "card_id": card_id,
                "card_title": card.title,
                "message": "Card was updated but remains incomplete. Fill missing fields, then save in frontend to trigger workflow.",
                "is_complete": False,
                "completion_status": "incomplete",
                "warning": f"Missing required fields: {missing_fields_str}",
                "missing_fields": result["missing_fields"],
                "current_data": result["data"],
                "applied": result["applied"],
                "failed": result["failed"],
                "needs_confirmation": True
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Update failed: {str(e)}"
        }


@tool
def update_card(
    card_id: int,
    instructions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Assistant tool: update_card."""
    return _update_card_impl(card_id, instructions)


@tool
def modify_card_field(
    card_id: int,
    field_path: str,
    new_value: Any,
) -> Dict[str, Any]:
    """Assistant tool: modify_card_field."""
    path = "/" + field_path if not field_path.startswith("/") else field_path
    instruction = {"op": "set", "path": path, "value": new_value}

    return _update_card_impl(card_id=card_id, instructions=[instruction])


@tool
def get_card_type_schema(
    card_type_name: str,
) -> Dict[str, Any]:
    """Assistant tool: get_card_type_schema."""

    deps = _get_deps()

    logger.info(f" [Assistant.get_card_type_schema] card_type={card_type_name}")

    result = get_card_type_schema_payload(
        deps.session,
        card_type_name,
        allow_model_name=False,
        require_schema=False,
    )

    if not result.get("success"):
        logger.warning(
            f"[Assistant.get_card_type_schema] Card type {card_type_name!r} does not exist"
        )
        return {
            "success": False,
            "error": f"Card type {card_type_name!r} does not exist"
        }

    output = {
        "success": True,
        "card_type": result.get("card_type") or card_type_name,
        "schema": result.get("schema") or {},
        "description": f"Complete schema definition for card type {card_type_name!r}"
    }

    return output


@tool
def get_card_content(
    card_id: int,
) -> Dict[str, Any]:
    """Assistant tool: get_card_content."""

    deps = _get_deps()

    logger.info(f" [Assistant.get_card_content] card_id={card_id}")

    card = deps.session.query(Card).filter(Card.id == card_id).first()

    if not card:
        return {
            "success": False,
            "error": f"Card #{card_id} does not exist"
        }

    result = {
        "success": True,
        "card_id": card.id,
        "title": card.title,
        "card_type": card.card_type.name if card.card_type else "Unknown",
        "parent_id": card.parent_id,  # parent card id for hierarchy
        "content": card.content or {},
        "created_at": str(card.created_at) if card.created_at else None
    }

    if card.parent_id and card.parent:
        result["parent_title"] = card.parent.title
        result["parent_type"] = card.parent.card_type.name if card.parent.card_type else "Unknown"

    logger.info(
        f"[Assistant.get_card_content] Returned card content (parent_id={card.parent_id})"
    )
    return result


@tool
def replace_field_text(
    card_id: int,
    field_path: str,
    old_value: str,
    new_value: str,
) -> Dict[str, Any]:
    """Assistant tool: replace_field_text."""

    deps = _get_deps()

    logger.info(f" [Assistant.replace_field_text] card_id={card_id}, path={field_path}")

    try:
        # Use CardService logic directly
        service = CardService(deps.session)
        result = service.replace_field_text(
            card_id=card_id,
            field_path=field_path,
            old_text=old_value,
            new_text=new_value,
            fuzzy_match=True
        )

        if not result.get("success"):
            raw_error = str(result.get("error") or "Replace failed")
            raw_hint = str(result.get("hint") or "").strip()

            suggestion = ""
            if raw_error in ("Specified source fragment not found", "Start text not found", "End text not found", "Invalid fuzzy match format"):
                suggestion = "Call get_card_content first, copy the latest exact fragment, then retry. For long text use start...end format."
            elif "is not text" in raw_error:
                suggestion = "Target field is not string text; use modify_card_field for structured update."
            elif "Field path" in raw_error:
                suggestion = "Field path may be wrong; inspect card structure and confirm field_path."

            if suggestion:
                result["message"] = f"Text replace failed: {raw_error}. {suggestion}"
            else:
                result["message"] = f"Text replace failed: {raw_error}."

            if raw_hint:
                result["message"] = f"{result['message']} (location hint: {raw_hint})"

            logger.warning(
                f"[Assistant.replace_field_text] Replace failed: {result.get('error')}"
            )
            return result

        # Service already commits, but tool flow often expects us to handle it or just be sure.
        # CardService.replace_field_text does commit.


        result["message"] = (
            f"Replaced text in {result.get('card_title')!r} field {field_path}: "
            f"{result.get('replaced_count')} occurrences"
        )

        return result

    except Exception as e:
        return {"success": False, "error": f"Replace failed: {str(e)}"}


@tool
def replace_card_text_by_lines(
    card_id: int,
    field_path: str,
    start_line: int,
    end_line: int,
    new_text: str,
    snapshot_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Assistant tool: replace_card_text_by_lines."""
    deps = _get_deps()
    logger.info(
        f"🧩 [Assistant.replace_card_text_by_lines] card_id={card_id}, "
        f"path={field_path}, lines={start_line}-{end_line}"
    )

    try:
        service = CardService(deps.session)
        result = service.replace_field_text_by_lines(
            card_id=card_id,
            field_path=field_path,
            start_line=start_line,
            end_line=end_line,
            new_text=new_text,
            snapshot_hash=snapshot_hash,
        )
        if not result.get("success"):
            raw_error = str(result.get("error") or "Line replace failed")
            if "Snapshot check failed" in raw_error or "Original fragment check failed" in raw_error:
                result["message"] = (
                    f"{raw_error}. Reference the latest body fragment, then retry line replacement."
                )
            else:
                result["message"] = f"Line replace failed: {raw_error}"
            return result

        result["message"] = (
            f"Replaced lines {start_line}-{end_line}; "
            f"changed {result.get('replaced_line_count')} lines to {result.get('new_line_count')} lines; "
            f"target field: {field_path}"
        )
        return result
    except Exception as e:
        return {"success": False, "error": f"Line replace failed: {str(e)}"}


@tool
def list_reviews_for_target(
    target_id: int,
    review_type: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """Assistant tool: list_reviews_for_target."""
    deps = _get_deps()
    logger.info(
        f"📚 [Assistant.list_reviews_for_target] target_id={target_id}, review_type={review_type}, limit={limit}"
    )
    try:
        review_card_type = get_card_type_by_identifier(deps.session, REVIEW_RESULT_CARD_TYPE_NAME)
        if not review_card_type:
            return {"success": False, "error": f"Missing card type: {REVIEW_RESULT_CARD_TYPE_NAME}"}

        rows = (
            deps.session.query(Card)
            .filter(Card.project_id == deps.project_id, Card.card_type_id == review_card_type.id)
            .order_by(Card.created_at.desc())
            .all()
        )
        filtered = []
        for row in rows:
            content = dict(row.content or {})
            if int(content.get("review_target_card_id") or -1) != target_id:
                continue
            if review_type and review_type != "all" and str(content.get("review_type") or "") != review_type:
                continue
            filtered.append(row)
        filtered = filtered[: max(1, min(limit, 100))]
        return {
            "success": True,
            "count": len(filtered),
            "reviews": [
                {
                    "review_card_id": row.id,
                    "project_id": row.project_id,
                    "target_id": int((row.content or {}).get("review_target_card_id") or 0),
                    "target_title": (row.content or {}).get("review_target_title"),
                    "review_type": (row.content or {}).get("review_type"),
                    "review_profile": (row.content or {}).get("review_profile"),
                    "target_field": (row.content or {}).get("review_target_field"),
                    "quality_gate": (row.content or {}).get("quality_gate"),
                    "prompt_name": (row.content or {}).get("prompt_name"),
                    "created_at": (row.content or {}).get("reviewed_at") or str(row.created_at),
                    "title": row.title,
                }
                for row in filtered
            ],
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to get review records: {str(e)}"}


@tool
def get_review_record(review_id: int) -> Dict[str, Any]:
    """Assistant tool: get_review_record."""
    deps = _get_deps()
    logger.info(f"📄 [Assistant.get_review_record] review_card_id={review_id}")
    try:
        row = deps.session.get(Card, review_id)
        review_card_type = get_card_type_by_identifier(deps.session, REVIEW_RESULT_CARD_TYPE_NAME)
        if not row or row.project_id != deps.project_id or not review_card_type or row.card_type_id != review_card_type.id:
            return {"success": False, "error": f"Review result card #{review_id} does not exist"}
        content = dict(row.content or {})
        return {
            "success": True,
            "review": {
                "review_card_id": row.id,
                "project_id": row.project_id,
                "target_id": int(content.get("review_target_card_id") or 0),
                "target_title": content.get("review_target_title"),
                "review_type": content.get("review_type"),
                "review_profile": content.get("review_profile"),
                "target_field": content.get("review_target_field"),
                "quality_gate": content.get("quality_gate"),
                "prompt_name": content.get("prompt_name"),
                "result_text": content.get("review_markdown"),
                "content_snapshot": content.get("target_snapshot"),
                "meta": content.get("meta"),
                "created_at": content.get("reviewed_at") or str(row.created_at),
                "title": row.title,
            },
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read review record: {str(e)}"}


@tool
def delete_card(
    card_id: int,
    skip_confirmation: bool = False
) -> Dict[str, Any]:
    """Assistant tool: delete_card."""
    deps = _get_deps()

    logger.info(f"🗑️ [Assistant.delete_card] card_id={card_id}, skip_confirmation={skip_confirmation}")

    try:
        card = _get_card_by_id(deps.session, card_id, deps.project_id)
        if not card:
            result = CardOperationResult(
                success=False,
                status=ToolResultStatus.FAILED,
                message=f"Card ID={card_id} does not exist or does not belong to current project",
                error=f"Card ID={card_id} does not exist"
            )
            return to_dict(result)

        child_count = deps.session.query(Card).filter(
            Card.parent_id == card_id
        ).count()

        if not skip_confirmation:
            warning = None
            if child_count > 0:
                warning = f"This card has {child_count} child cards; deleting it will also delete children"

            result = ConfirmationRequest(
                confirmation_id=str(uuid.uuid4()),
                action="delete_card",
                action_params={"card_id": card_id},
                message=f"Confirm deleting card {card.title!r}. Ask user to explicitly say \"confirm delete\" or \"cancel\"",
                warning=warning,
                data={
                    "card_id": card_id,
                    "card_title": card.title,
                    "card_type": card.card_type.name,
                    "child_count": child_count
                }
            )
            return to_dict(result)


        if child_count > 0:
            deps.session.query(Card).filter(Card.parent_id == card_id).delete()

        card_title = card.title
        deps.session.delete(card)
        deps.session.commit()

        result = CardOperationResult(
            success=True,
            status=ToolResultStatus.SUCCESS,
            message=f"Card {card_title!r} deleted successfully" + (f" (including {child_count} child cards)" if child_count > 0 else ""),
            card_id=card_id,
            card_title=card_title,
            data={"deleted_children": child_count}
        )
        return to_dict(result)

    except Exception as e:
        result = CardOperationResult(
            success=False,
            status=ToolResultStatus.FAILED,
            message=f"\u5220\u9664\u5931\u8d25: {str(e)}",
            error=str(e)
        )
        return to_dict(result)


@tool
def move_card(
    card_id: int,
    new_parent_id: Optional[int] = None,
    skip_confirmation: bool = False
) -> Dict[str, Any]:
    """Assistant tool: move_card."""
    deps = _get_deps()

    logger.info(f"📦 [Assistant.move_card] card_id={card_id}, new_parent={new_parent_id}, skip_confirmation={skip_confirmation}")

    try:
        card = _get_card_by_id(deps.session, card_id, deps.project_id)
        if not card:
            result = CardOperationResult(
                success=False,
                status=ToolResultStatus.FAILED,
                message=f"\u5361\u7247 ID={card_id} \u4e0d\u5b58\u5728\u6216\u4e0d\u5c5e\u4e8e\u5f53\u524d\u9879\u76ee",
                error=f"\u5361\u7247 ID={card_id} \u4e0d\u5b58\u5728"
            )
            return to_dict(result)

        new_parent = None
        if new_parent_id is not None:
            new_parent = _get_card_by_id(deps.session, new_parent_id, deps.project_id)
            if not new_parent:
                result = CardOperationResult(
                    success=False,
                    status=ToolResultStatus.FAILED,
                    message=f"\u76ee\u6807\u7236\u5361\u7247 ID={new_parent_id} \u4e0d\u5b58\u5728\u6216\u4e0d\u5c5e\u4e8e\u5f53\u524d\u9879\u76ee",
                    error=f"\u76ee\u6807\u7236\u5361\u7247\u4e0d\u5b58\u5728"
                )
                return to_dict(result)

            if new_parent_id == card_id:
                result = CardOperationResult(
                    success=False,
                    status=ToolResultStatus.FAILED,
                    message="Cannot move a card under itself",
                    error="Circular reference error"
                )
                return to_dict(result)


        old_parent = None
        old_parent_title = "Root"
        if card.parent_id:
            old_parent = deps.session.get(Card, card.parent_id)
            if old_parent:
                old_parent_title = f"《{old_parent.title}》"

        new_parent_title = "Root" if not new_parent else f"《{new_parent.title}》"

        if not skip_confirmation:
            result = ConfirmationRequest(
                confirmation_id=str(uuid.uuid4()),
                action="move_card",
                action_params={
                    "card_id": card_id,
                    "new_parent_id": new_parent_id
                },
                message=f"❓ \u786e\u8ba4\u8981\u5c06\u5361\u7247《{card.title}》\u4ece {old_parent_title} \u79fb\u52a8\u5230 {new_parent_title} \u5417？\u8bf7\u7528\u6237\u660e\u786e\u8bf4\"\u786e\u8ba4\u79fb\u52a8\"\u6216\"\u53d6\u6d88\"",
                data={
                    "card_id": card_id,
                    "card_title": card.title,
                    "from_parent": old_parent_title,
                    "to_parent": new_parent_title
                }
            )
            return to_dict(result)


        card.parent_id = new_parent_id
        deps.session.commit()

        result = CardOperationResult(
            success=True,
            status=ToolResultStatus.SUCCESS,
            message=f"✅ \u5361\u7247《{card.title}》\u5df2\u4ece {old_parent_title} \u79fb\u52a8\u5230 {new_parent_title}",
            card_id=card_id,
            card_title=card.title,
            data={
                "from_parent": old_parent_title,
                "to_parent": new_parent_title
            }
        )
        return to_dict(result)

    except Exception as e:
        result = CardOperationResult(
            success=False,
            status=ToolResultStatus.FAILED,
            message=f"\u79fb\u52a8\u5931\u8d25: {str(e)}",
            error=str(e)
        )
        return to_dict(result)


ASSISTANT_TOOLS = [
    search_cards,
    create_card,
    update_card,
    modify_card_field,
    delete_card,
    move_card,
    replace_card_text_by_lines,
    replace_field_text,
    list_reviews_for_target,
    get_review_record,
    get_card_type_schema,
    get_card_content,
]

ASSISTANT_TOOL_REGISTRY = {tool.name: tool for tool in ASSISTANT_TOOLS}

ASSISTANT_TOOL_DESCRIPTIONS = {
    tool.name: {
        "description": tool.description,
        "args": tool.args,
    }
    for tool in ASSISTANT_TOOLS
}
