
from app.locales import localized_text
import asyncio
import threading
from typing import List, Dict, Any
from sqlmodel import Session, select
from time import monotonic
from loguru import logger

from app.db.models import Card, Workflow, WorkflowRun
from app.services.workflow.engine import StateManager
from app.services.workflow.engine.runtime import workflow_runtime
from app.db.session import engine as db_engine
from app.core import on_event, Event

_recent_keys: Dict[str, float] = {}
_DEBOUNCE_MS = 1500


def _make_idempotency_key(event: str, workflow_id: int, card: Card | None, project_id: int | None) -> str:
    card_id = getattr(card, "id", None) or 0
    proj_id = project_id or getattr(card, "project_id", None) or 0
    return f"evt:{event}|wf:{workflow_id}|card:{card_id}|proj:{proj_id}"


def _should_suppress(session: Session, key: str, workflow_id: int) -> bool:
    now = monotonic()
    last = _recent_keys.get(key)
    if last is not None and (now - last) * 1000 < _DEBOUNCE_MS:
        return True

    try:
        for k, v in list(_recent_keys.items()):
            if (now - v) * 1000 > 60000:
                _recent_keys.pop(k, None)
    except Exception:
        pass

    _recent_keys[key] = now
    return False


def _get_value_by_path(obj: Any, path: str) -> Any:
    parts = path.split('.')
    current = obj

    for part in parts:
        if current is None:
            return None

        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)

    return current


def _check_condition(value: Any, op: str, target: Any) -> bool:
    if op == "eq" or op == "==":
        return value == target
    elif op == "neq" or op == "!=":
        return value != target
    elif op == "contains":
        if isinstance(value, (list, str, dict)):
            return target in value
        return False
    elif op == "not_contains":
        if isinstance(value, (list, str, dict)):
            return target not in value
        return True
    elif op == "gt" or op == ">":
        try:
            return float(value) > float(target)
        except (ValueError, TypeError):
            return False
    elif op == "lt" or op == "<":
        try:
            return float(value) < float(target)
        except (ValueError, TypeError):
            return False
    elif op == "exists":
        if target:  # If target is true, check if exists (not None)
            return value is not None
        else:      # If target is false, check if not exists (is None)
            return value is None
    return False


def _evaluate_filter(card: Card, filter_config: Dict, old_content: Dict | None = None) -> bool:
    if not filter_config:
        return True

    conditions = filter_config.get("conditions", [])
    if not conditions:
        return True

    operator = filter_config.get("operator", "and").lower()
    results = []

    old_obj = {"content": old_content} if old_content else {}

    for cond in conditions:
        field = cond.get("field")
        op = cond.get("op", "eq")
        target = cond.get("value")

        if not field:
            continue

        value = _get_value_by_path(card, field)

        if op == "changed":
            old_value = _get_value_by_path(old_obj, field)
            if old_content is None:
                res = True
            else:
                res = value != old_value
        else:
            res = _check_condition(value, op, target)

        results.append(res)

        if operator == "and" and not res:
            return False
        if operator == "or" and res:
            return True

    if operator == "and":
        return all(results)
    else:  # or
        return any(results)


def _match_triggers_for_card(session: Session, event: str, card: Card, is_created: bool = False, old_content: Dict | None = None) -> List[Dict[str, Any]]:
    from app.services.workflow.trigger_extractor import get_active_triggers_by_event

    if card.card_type is None and card.card_type_id:
        session.refresh(card, ["card_type"])

    card_type_name = card.card_type.name if card.card_type else None

    event_name = "card.saved" if event == "onsave" else event
    event_data = {
        "card_id": card.id,
        "project_id": card.project_id,
        "card_type": card_type_name,
        "is_created": bool(is_created),
    }
    all_triggers = get_active_triggers_by_event(session, event_name, event_data)

    matched: List[Dict[str, Any]] = []
    current_event = "create" if is_created else "update"

    for t in all_triggers:
        filter_json = t.get("filter_json")

        if filter_json:
            if "events" in filter_json:
                allowed_events = filter_json["events"]
                if current_event not in allowed_events:
                    continue

            if "conditions" in filter_json:
                if not _evaluate_filter(card, filter_json, old_content):
                    continue

        matched.append(t)
    return matched


def _async_execute_workflow(run_id: int):
    async def _execute():
        session = Session(db_engine)
        try:
            workflow_runtime.register_task(run_id)

            slot_status = await workflow_runtime.acquire_slot(run_id)
            if slot_status == "cancelled":
                StateManager(session).update_run_status(run_id, "cancelled")
                return
            if slot_status == "paused":
                StateManager(session).update_run_status(run_id, "paused")
                return

            state_manager = StateManager(session)
            run = session.get(WorkflowRun, run_id)
            if not run:
                return

            wf = session.get(Workflow, run.workflow_id)
            if not wf:
                return

            state_manager.update_run_status(run_id, "running")

            try:
                await _execute_code_workflow(session, state_manager, run, wf)
            except asyncio.CancelledError:
                state_manager.update_run_status(run_id, "cancelled")
                return
            except Exception as e:
                state_manager.update_run_status(run_id, "failed")
                state_manager.save_error(run_id, str(e))
                raise

        except Exception as e:
            pass
        finally:
            workflow_runtime.finish_run(
                run_id,
                keep_pause=workflow_runtime.is_pause_requested(run_id)
            )
            session.close()

    try:
        try:
            # Check if we are in a running loop (async context)
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(_execute())
        else:
            # Sync endpoints run in a threadpool; start a background loop so the
            # request can return while the workflow keeps running.
            thread = threading.Thread(
                target=lambda: asyncio.run(_execute()),
                name=f"workflow-run-{run_id}",
                daemon=True,
            )
            thread.start()

    except Exception as e:




        pass
async def _execute_code_workflow(
    session: Session,
    state_manager: StateManager,
    run: WorkflowRun,
    workflow: Workflow,
) -> None:
    from .engine.async_executor import AsyncExecutor
    from .parser.marker_parser import WorkflowParser

    run_id = run.id
    code = workflow.definition_code or ""

    if not code:
        raise ValueError(localized_text('hardcoded.services_workflow_triggers_bea4e784'))


    parser = WorkflowParser()
    plan = parser.parse(code)


    initial_context = {}

    trigger_data = {}
    if run.scope_json:
        trigger_data.update(run.scope_json)
    if run.params_json:
        trigger_data.update(run.params_json)

    if trigger_data:
        initial_context["__trigger_data__"] = trigger_data

    executor = AsyncExecutor(
        session=session,
        state_manager=state_manager,
        run_id=run_id
    )

    workflow_runtime.register_executor(run_id, executor)
    try:
        async for event in executor.execute_stream(plan, initial_context):
            if event.type == "error":
                pass
            elif event.type == "complete":


                pass
        if executor.is_paused or workflow_runtime.is_pause_requested(run_id):
            state_manager.update_run_status(run_id, "paused")
            return
    finally:
        workflow_runtime.unregister_executor(run_id, executor)

    state_manager.update_run_status(
        run_id,
        "succeeded",
        summary_json={
            "variables": list(executor.context.keys()),
            "outputs": executor.context
        }
    )



def _execute_triggers(session: Session, event_name: str, triggers: List[Dict[str, Any]],
                     scope: Dict, card: Card | None = None, project_id: int | None = None,
                     payload: Dict[str, Any] | None = None) -> List[int]:
    from .engine import RunManager

    run_ids: List[int] = []

    run_manager = RunManager(session)

    for t in triggers:
        workflow_id = t.get("workflow_id")
        if not workflow_id:
            continue

        wf = session.get(Workflow, workflow_id)
        if not wf:
            logger.warning(f"[Trigger] Workflow {workflow_id} not found")
            continue
        if not wf.is_active:
            continue

        idem_key = _make_idempotency_key(event_name, workflow_id, card, project_id)
        if _should_suppress(session, idem_key, workflow_id):
            logger.debug(f"[Trigger] Trigger suppressed by idempotency: {idem_key}")
            continue

        try:
            serializable_payload = {}
            if payload:
                for key, value in payload.items():
                    if key in ['session', 'card']:
                        continue
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        serializable_payload[key] = value

            if "card_type" not in serializable_payload:
                resolved_card_type = payload.get("card_type") if payload else None
                if resolved_card_type is None and card is not None:
                    card_type = getattr(card, "card_type", None)
                    if card_type is None and getattr(card, "card_type_id", None):
                        try:
                            session.refresh(card, ["card_type"])
                            card_type = getattr(card, "card_type", None)
                        except Exception:
                            card_type = None
                    resolved_card_type = getattr(card_type, "name", None) if card_type else None
                if isinstance(resolved_card_type, str):
                    serializable_payload["card_type"] = resolved_card_type

            run = run_manager.create_run(
                workflow_id=workflow_id,
                trigger_data=scope,
                params=serializable_payload,
                idempotency_key=idem_key
            )

            if run.id:
                run_ids.append(int(run.id))

                try:
                    from app.core.workflow_context import add_triggered_run_id
                    add_triggered_run_id(int(run.id))
                except Exception:
                    pass

                _async_execute_workflow(run.id)
            else:
                 logger.error(f"[Trigger] Run creation returned no ID for wf {workflow_id}")

        except Exception as e:


            pass
    return run_ids


@on_event("card.saved")
def handle_card_saved(event: Event):
    session: Session = event.data.get("session")
    card: Card = event.data.get("card")

    if not session or not card:
        return

    is_created = event.data.get("is_created", False)

    card_type_name = event.data.get("card_type")
    if card_type_name is None:
        card_type = getattr(card, "card_type", None)
        if card_type is None and getattr(card, "card_type_id", None):
            try:
                session.refresh(card, ["card_type"])
                card_type = getattr(card, "card_type", None)
            except Exception:
                card_type = None
        card_type_name = getattr(card_type, "name", None) if card_type else None

    triggers = _match_triggers_for_card(session, "onsave", card, is_created=is_created)
    scope = {
        "card_id": card.id,
        "project_id": card.project_id,
        "card_type": card_type_name,
        "is_created": bool(is_created),
    }
    run_ids = _execute_triggers(session, "onsave", triggers, scope, card, card.project_id, payload=event.data)

    event.data["triggered_run_ids"] = run_ids
    if run_ids:




        pass
@on_event("project.created")
def handle_project_created(event: Event):
    from app.services.workflow.trigger_extractor import get_active_triggers_by_event

    try:
        session: Session = event.data.get("session")
        project_id: int = event.data.get("project_id")
        template: str | None = event.data.get("template")

        if not session or not project_id:
            return

        if template is None:
            event.data["triggered_run_ids"] = []
            return

        event_data = {
            "project_id": project_id,
            "template": template,
            "user_id": event.data.get("user_id"),
        }

        triggers = get_active_triggers_by_event(session, "project.created", event_data)

        scope = {"project_id": project_id, "template": template}
        run_ids = _execute_triggers(session, "project.created", triggers, scope, None, project_id, payload=event.data)

        event.data["triggered_run_ids"] = run_ids

        if run_ids:
            pass
    except Exception as e:


        pass
