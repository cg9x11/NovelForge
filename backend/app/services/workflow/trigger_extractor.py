
from typing import List, Dict, Any
from loguru import logger
from app.services.card_type_service_utils import resolve_card_type_key


def extract_triggers_from_code(code: str) -> List[Dict[str, Any]]:
    from app.services.workflow.parser.marker_parser import WorkflowParser

    if not code or not code.strip():
        return []

    NODE_TYPE_TO_EVENT = {
        "Trigger.ProjectCreated": "project.created",
        "Trigger.CardSaved": "card.saved",
    }

    try:
        parser = WorkflowParser()
        plan = parser.parse(code)

        triggers = []

        for stmt in plan.statements:
            if stmt.disabled:
                continue

            node_type = stmt.node_type
            config = stmt.config or {}

            event = NODE_TYPE_TO_EVENT.get(node_type)
            if not event:
                continue

            match = {}

            if node_type == "Trigger.ProjectCreated":
                if "template" in config and config["template"]:
                    match["template"] = config["template"]

            elif node_type == "Trigger.CardSaved":
                if "card_type" in config and config["card_type"]:
                    match["card_type"] = config["card_type"]
                on_create = bool(config.get("on_create", False))
                on_update = bool(config.get("on_update", True))

                if not on_create and not on_update:
                    continue

                if on_create and not on_update:
                    match["is_created"] = True
                elif not on_create and on_update:
                    match["is_created"] = False

            trigger_config = {
                "event": event,
                "match": match if match else None
            }

            triggers.append(trigger_config)

        return triggers

    except Exception as e:
        return []


def sync_triggers_cache(workflow, session) -> None:
    if not workflow.definition_code:
        workflow.triggers_cache = []
        return

    triggers = extract_triggers_from_code(workflow.definition_code)

    workflow.triggers_cache = triggers
    session.add(workflow)



def match_event(event_name: str, event_data: Dict[str, Any], trigger: Dict[str, Any]) -> bool:
    if trigger.get("event") != event_name:
        return False

    match_conditions = trigger.get("match")
    if not match_conditions:
        return True

    for key, expected_value in match_conditions.items():
        actual_value = event_data.get(key)

        if key == "card_type":
            actual_key = resolve_card_type_key(actual_value) or actual_value
            expected_key = resolve_card_type_key(expected_value) or expected_value
            if actual_key != expected_key:
                return False
            continue

        if actual_value != expected_value:
            return False

    return True


def get_active_triggers_by_event(session, event_name: str, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    from sqlmodel import select
    from app.db.models import Workflow

    stmt = select(Workflow).where(
        Workflow.is_active == True,
        Workflow.triggers_cache.isnot(None)
    )
    workflows = session.exec(stmt).all()

    matched_triggers = []

    for wf in workflows:
        if not wf.triggers_cache:
            continue

        for trigger in wf.triggers_cache:
            if match_event(event_name, event_data, trigger):
                matched_triggers.append({
                    "workflow_id": wf.id,
                    **trigger
                })

    return matched_triggers
