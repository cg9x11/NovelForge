from app.locales import localized_text
from app.locales import schema_field_description
from typing import List, Optional, Dict, Any
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from datetime import datetime
from loguru import logger

from app.db.session import get_session
from app.db.models import Workflow, WorkflowRun
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowRead,
    WorkflowRunRead,
    RunRequest,
    CancelResponse,
    RunStatus,
    NodeTypesResponse,
)
from app.schemas.workflow_agent import WorkflowPatchRequest, WorkflowPatchResponse
from app.services.workflow.patcher import (
    compute_code_revision,
    execute_patch_with_validation,
    parse_workflow_code_to_result,
)


PROJECT_TEMPLATE_LABELS = {
    "snowflake": {
        "name": "Tạo dự án - Phương pháp bông tuyết",
        "description": "Workflow tích hợp để tạo dự án bằng phương pháp bông tuyết",
    },
}


def _clean_dollar_prefix(value: Any) -> Any:
    if isinstance(value, str):
        if value.startswith('$'):
            if value.startswith('${') and value.endswith('}'):
                return value[2:-1]
            else:
                return value[1:]
        return value
    elif isinstance(value, list):
        return [_clean_dollar_prefix(item) for item in value]
    elif isinstance(value, dict):
        return {
            _clean_dollar_prefix(k): _clean_dollar_prefix(v)
            for k, v in value.items()
        }
    else:
        return value
from app.services.workflow import (
    get_node_types,
    get_all_node_metadata,
    RunManager
)
from app.services.workflow.engine.runtime import workflow_runtime


router = APIRouter()


@router.get("/nodes/types", response_model=NodeTypesResponse)
def get_node_types_api():
    all_metadata = get_all_node_metadata()

    node_info = []
    for meta in all_metadata:
        node_info.append({
            "type": meta.type,
            "category": meta.category,
            "label": meta.label,
            "description": meta.description,
            "documentation": meta.documentation,
            "input_schema": meta.input_schema,
            "output_schema": meta.output_schema
        })

    return {"node_types": node_info}





@router.get("/workflow-node-types/categories")
def get_node_categories():
    all_metadata = get_all_node_metadata()
    categories = {}

    for meta in all_metadata:
        if meta.category not in categories:
            categories[meta.category] = []
        categories[meta.category].append({
            'type': meta.type,
            'label': meta.label,
            'description': meta.description
        })

    return {'categories': categories}


@router.get("/nodes/{node_type}/metadata")
def get_node_metadata_api(node_type: str):
    from app.services.workflow.registry import get_node_metadata as get_registry_metadata

    registry_meta = get_registry_metadata(node_type)
    if not registry_meta:
        raise HTTPException(status_code=404, detail=f"Node type not found: {node_type}")

    outputs = []
    if registry_meta.output_schema and "properties" in registry_meta.output_schema:
        for field_name, field_def in registry_meta.output_schema["properties"].items():
            outputs.append({
                "name": field_name,
                "type": field_def.get("type", "any"),
                "description": field_def.get("description", "")
            })

    metadata = {
        "type": registry_meta.type,
        "category": registry_meta.category,
        "label": registry_meta.label,
        "description": registry_meta.description,
        "documentation": registry_meta.documentation,
        "input_schema": registry_meta.input_schema,
        "output_schema": registry_meta.output_schema,
        "outputs": outputs
    }

    return metadata





@router.get("/workflows", response_model=List[WorkflowRead])
def list_workflows(session: Session = Depends(get_session)):
    return session.exec(select(Workflow)).all()


@router.post("/workflows", response_model=WorkflowRead)
def create_workflow(payload: WorkflowCreate, session: Session = Depends(get_session)):
    wf = Workflow(**payload.model_dump())
    session.add(wf)
    session.commit()
    session.refresh(wf)

    from app.services.workflow.trigger_extractor import sync_triggers_cache
    sync_triggers_cache(wf, session)

    session.commit()

    return wf


@router.get("/workflows/project-templates")
def get_project_templates(session: Session = Depends(get_session)):
    stmt = select(Workflow).where(Workflow.is_active == True)
    workflows = session.exec(stmt).all()

    templates = []

    for wf in workflows:
        if not wf.triggers_cache:
            continue

        for trigger in wf.triggers_cache:
            if trigger.get("event") == "project.created":
                match = trigger.get("match") or {}
                template_id = match.get("template")

                label = PROJECT_TEMPLATE_LABELS.get(template_id or "", {})
                templates.append({
                    "workflow_id": wf.id,
                    "workflow_name": label.get("name", wf.name),
                    "template": template_id,
                    "description": label.get("description", wf.description)
                })

    return {"templates": templates}


@router.get("/workflows/{workflow_id}", response_model=WorkflowRead)
def get_workflow(workflow_id: int, session: Session = Depends(get_session)):
    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.put("/workflows/{workflow_id}", response_model=WorkflowRead)
def update_workflow(workflow_id: int, payload: WorkflowUpdate, session: Session = Depends(get_session)):
    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(wf, k, v)

    wf.updated_at = datetime.utcnow()
    session.add(wf)
    session.commit()
    session.refresh(wf)

    from app.services.workflow.trigger_extractor import sync_triggers_cache
    sync_triggers_cache(wf, session)
    session.commit()

    return wf


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, session: Session = Depends(get_session)):
    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    session.delete(wf)
    session.commit()
    return {"ok": True}


@router.get("/workflows/runs/{run_id}", response_model=WorkflowRunRead)
def get_run(run_id: int, session: Session = Depends(get_session)):
    run = session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/workflows/{workflow_id}/runs", response_model=List[WorkflowRunRead])
def list_workflow_runs(
    workflow_id: int,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    from sqlmodel import select, desc

    stmt = select(WorkflowRun).where(
        WorkflowRun.workflow_id == workflow_id
    )

    if status:
        stmt = stmt.where(WorkflowRun.status == status)

    stmt = stmt.order_by(
        desc(WorkflowRun.created_at)
    ).limit(limit).offset(offset)

    runs = session.exec(stmt).all()
    return runs


@router.get("/runs", response_model=List[WorkflowRunRead])
def list_all_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    from sqlmodel import select, desc
    import logging
    logger = logging.getLogger(__name__)

    stmt = select(WorkflowRun).order_by(desc(WorkflowRun.created_at))

    if status:
        stmt = stmt.where(WorkflowRun.status == status)

    stmt = stmt.limit(limit).offset(offset)

    runs = session.exec(stmt).all()

    if runs:


        pass
    pass
    return runs


@router.post("/workflows/{workflow_id}/validate")
def validate_workflow_endpoint(workflow_id: int, session: Session = Depends(get_session)):
    from app.services.workflow.validator import validate_workflow

    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    code = wf.definition_code or ""

    if not code:
        return {
            "is_valid": False,
            "errors": [{
                "line": 0,
                "variable": "",
                "error_type": "syntax",
                "message": localized_text('hardcoded.api_endpoints_workflows_bea4e784'),
                "suggestion": None
            }],
            "warnings": []
        }

    result = validate_workflow(code, session=session)

    return result.to_dict()


@router.post("/workflows/runs/{run_id}/cancel", response_model=CancelResponse)
async def cancel_run(run_id: int, session: Session = Depends(get_session)):
    run_manager = RunManager(session)
    ok = await run_manager.cancel_run(run_id)
    return CancelResponse(ok=ok, message="cancelled" if ok else "not running")


@router.post("/workflows/runs/{run_id}/pause")
async def pause_run(run_id: int, session: Session = Depends(get_session)):

    run = session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status == "paused":
        return {"ok": True, "message": "paused"}

    if run.status not in ["running", "queued"]:
        raise HTTPException(status_code=400, detail=f"Cannot pause run with status {run.status}")

    if not workflow_runtime.request_pause(run_id):


        pass
    run.status = "paused"
    session.add(run)
    session.commit()

    return {"ok": True, "message": "paused"}


@router.post("/workflows/runs/{run_id}/resume")
async def resume_run(run_id: int, session: Session = Depends(get_session)):
    run_manager = RunManager(session)
    ok = await run_manager.resume_run(run_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot resume run: run not found or not paused")
    return {"ok": True, "message": "resumed"}


@router.get("/workflows/{workflow_id}/execute-stream")
async def execute_code_workflow_stream(
    workflow_id: int,
    resume: bool = False,
    run_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    import json
    from app.services.workflow.parser.marker_parser import WorkflowParser
    from app.services.workflow.engine.async_executor import AsyncExecutor
    from app.services.workflow.engine.state_manager import StateManager
    from app.services.workflow.registry import NodeRegistry

    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.is_active:
        raise HTTPException(status_code=400, detail="Workflow is not active")

    code = workflow.definition_code or ""
    if not code:
        raise HTTPException(status_code=400, detail="Workflow code is empty")

    run_manager = RunManager(session)

    if resume:
        if not run_id:
            raise HTTPException(status_code=400, detail="run_id is required when resume=True")

        run = session.get(WorkflowRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        if run.workflow_id != workflow_id:
            raise HTTPException(status_code=400, detail="Run does not belong to this workflow")

        workflow_runtime.request_resume(run_id)
    else:
        from datetime import datetime
        time_window = int(datetime.utcnow().timestamp() / 5)
        idempotency_key = f"manual_exec:{workflow_id}:{time_window}"

        run = run_manager.create_run(
            workflow_id=workflow_id,
            idempotency_key=idempotency_key
        )
        run_id = run.id

        if run.status == "running":
            pass
        else:


            pass
    async def event_stream():
        executor = None
        state_manager = StateManager(session)
        try:
            workflow_runtime.register_task(run_id)

            slot_status = await workflow_runtime.acquire_slot(run_id)
            if slot_status == "cancelled":
                state_manager.update_run_status(run_id, "cancelled")
                yield f"data: {json.dumps({'type': 'cancelled', 'message': localized_text('hardcoded.api_endpoints_workflows_cancelled')}, ensure_ascii=False)}\n\n"
                return
            if slot_status == "paused":
                state_manager.update_run_status(run_id, "paused")
                yield f"data: {json.dumps({'type': 'paused', 'message': localized_text('hardcoded.api_endpoints_workflows_paused')}, ensure_ascii=False)}\n\n"
                return

            state_manager.update_run_status(run_id, "running")

            from app.services.workflow.parser.marker_parser import WorkflowParser
            parser = WorkflowParser()
            plan = parser.parse(code)


            if not resume:
                from app.services.workflow.engine.execution_state import ExecutionState
                exec_state = ExecutionState(run_id)
                exec_state.clear_node_states(session)

            executor = AsyncExecutor(
                session=session,
                state_manager=state_manager,
                run_id=run_id
            )

            workflow_runtime.register_executor(run_id, executor)

            yield f"data: {json.dumps({'type': 'run_started', 'run_id': run_id}, ensure_ascii=False)}\n\n"

            async for event in executor.execute_stream(plan, initial_context={}):
                if executor.is_paused or workflow_runtime.is_pause_requested(run_id):
                    state_manager.update_run_status(run_id, "paused")
                    yield f"data: {json.dumps({'type': 'paused', 'message': localized_text('hardcoded.api_endpoints_workflows_paused')}, ensure_ascii=False)}\n\n"
                    return

                event_data = {
                    "type": event.type,
                    "statement": {
                        "variable": event.statement.variable,
                        "code": event.statement.code or f"{event.statement.variable} = {event.statement.node_type or 'expression'}(...)",
                        "line": event.statement.line_number,
                        "description": getattr(event.statement, 'description', '') or "",
                    }
                }

                if event.type == "start":
                    event_data["message"] = event.message or localized_text('hardcoded.api_endpoints_workflows_bbaf6bc3', event_statement_variable=event.statement.variable)
                elif event.type == "progress":
                    event_data["percent"] = event.percent
                    event_data["message"] = event.message
                elif event.type == "complete":
                    event_data["result"] = event.result
                    if event.message and localized_text('hardcoded.api_endpoints_workflows_486bfd90') in event.message:
                        event_data["resumed"] = True
                elif event.type == "error":
                    event_data["error"] = event.error

                try:
                    yield f"data: {json.dumps(event_data, ensure_ascii=False, default=str)}\n\n"
                except Exception as e:
                    executor.pause()
                    return

            state_manager.update_run_status(run_id, "succeeded")

            yield f"data: {json.dumps({'type': 'end', 'message': localized_text('hardcoded.api_endpoints_workflows_done')}, ensure_ascii=False)}\n\n"


        except asyncio.CancelledError:
            is_cancelled = workflow_runtime.is_cancel_requested(run_id)
            status = "cancelled" if is_cancelled else "paused"
            reason = localized_text('hardcoded.api_endpoints_workflows_4d0b4688') if is_cancelled else localized_text('hardcoded.api_endpoints_workflows_8e69d179')
            logger.info(f"[CodeWorkflow] {reason}: run_id={run_id}")
            try:
                state_manager.update_run_status(run_id, status)
            except:
                pass
            raise

        except Exception as e:




            try:
                state_manager = StateManager(session)
                state_manager.update_run_status(run_id, "failed")
            except:
                pass

            error_data = {
                "type": "error",
                "error": str(e),
                "message": localized_text('hardcoded.api_endpoints_workflows_68e6d117')
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        finally:
            if executor is not None:
                workflow_runtime.unregister_executor(run_id, executor)
            workflow_runtime.finish_run(
                run_id,
                keep_pause=workflow_runtime.is_pause_requested(run_id)
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/workflows/runs/{run_id}")
def delete_run(run_id: int, session: Session = Depends(get_session)):
    run = session.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status == "running":
        raise HTTPException(status_code=400, detail="Cannot delete a running record; pause or cancel it first")

    from app.db.models import NodeExecutionState
    stmt = select(NodeExecutionState).where(NodeExecutionState.run_id == run_id)
    node_states = session.exec(stmt).all()
    for node_state in node_states:
        session.delete(node_state)

    session.delete(run)
    session.commit()

    return {"ok": True, "message": "deleted"}


@router.get("/workflows/runs/{run_id}/status", response_model=RunStatus)
def get_run_status(run_id: int, session: Session = Depends(get_session)):
    run_manager = RunManager(session)
    status = run_manager.get_run_status(run_id)

    if not status:
        raise HTTPException(status_code=404, detail="Run not found")

    return status


@router.get("/workflows/templates")
def list_templates(session: Session = Depends(get_session)):
    stmt = select(Workflow).where(Workflow.is_template == True)
    templates = session.exec(stmt).all()
    return {"templates": templates}


@router.post("/workflows/from-template/{template_id}", response_model=WorkflowRead)
def create_from_template(
    template_id: int,
    name: str,
    session: Session = Depends(get_session)
):
    template = session.get(Workflow, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if not template.is_template:
        raise HTTPException(status_code=400, detail="Not a template")

    new_workflow = Workflow(
        name=name,
        description=localized_text('hardcoded.api_endpoints_workflows_ad333777', template_name=template.name),
        definition_code=template.definition_code,
        dsl_version=template.dsl_version,
        is_template=False
    )

    session.add(new_workflow)
    session.commit()
    session.refresh(new_workflow)

    from app.services.workflow.trigger_extractor import sync_triggers_cache
    sync_triggers_cache(new_workflow, session)
    session.commit()

    return new_workflow


# ============================================================
# ============================================================

@router.post("/workflows/parse")
def parse_workflow_code(payload: Dict[str, Any]):
    code = payload.get("code", "")
    if not code:
        return {"success": False, "errors": [localized_text('hardcoded.api_endpoints_workflows_26076a8a')]}

    parsed = parse_workflow_code_to_result(code)
    if not parsed.get("ok"):
        error = str(parsed.get("error") or "parse_failed")
        code_preview = "\n".join(
            f"{idx + 1}: {line[:180]}"
            for idx, line in enumerate(str(code or "").splitlines()[:12])
        )
        logger.error("[WorkflowParseAPI] parse failed: {}\ncode preview:\n{}", error, code_preview or "<empty>")
        return {
            "success": False,
            "errors": [error],
            "error": error,
            "debug": {"code_preview": code_preview},
        }

    statements = []
    for stmt in parsed.get("statements", []):
        variable = stmt.get("variable")
        cleaned_config = _clean_dollar_prefix(stmt.get("config"))
        statements.append({
            "variable": variable,
            "code": stmt.get("code") or (f"{variable} = ..." if variable else "..."),
            "line": stmt.get("line"),
            "node_type": stmt.get("node_type"),
            "config": cleaned_config,
            "is_async": bool(stmt.get("is_async")),
            "disabled": bool(stmt.get("disabled")),
            "description": stmt.get("description", "") or "",
        })

    return {
        "success": True,
        "statements": statements,
    }


@router.post("/workflows/rename-variable")
def rename_variable(payload: Dict[str, Any]):
    from app.services.workflow.parser.marker_renamer import rename_variable as marker_rename

    code = payload.get("code", "")
    old_name = payload.get("old_name", "")
    new_name = payload.get("new_name", "")


    if not code or not old_name or not new_name:
        return {"success": False, "error": localized_text('hardcoded.api_endpoints_workflows_fb565dcb')}

    try:
        new_code = marker_rename(code, old_name, new_name)


        return {
            "success": True,
            "new_code": new_code
        }
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/workflows/code", response_model=WorkflowRead)
def save_code_workflow(payload: Dict[str, Any], session: Session = Depends(get_session)):
    name = payload.get("name")
    code = payload.get("code")

    if not name or not code:
        raise HTTPException(status_code=400, detail="name and code cannot be empty")

    wf = Workflow(
        name=name,
        description=schema_field_description("try"),
        definition_code=code,
        dsl_version=2
    )

    session.add(wf)
    session.commit()
    session.refresh(wf)

    from app.services.workflow.trigger_extractor import sync_triggers_cache
    sync_triggers_cache(wf, session)
    session.commit()

    return wf


@router.get("/workflows/{workflow_id}/code")
def get_code_workflow(workflow_id: int, session: Session = Depends(get_session)):
    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": wf.id,
        "name": wf.name,
        "code": wf.definition_code or "",
        "revision": compute_code_revision(wf.definition_code or ""),
        "keep_run_history": wf.keep_run_history or False
    }


@router.post("/workflows/{workflow_id}/patch", response_model=WorkflowPatchResponse)
def patch_workflow_code(
    workflow_id: int,
    payload: WorkflowPatchRequest,
    session: Session = Depends(get_session),
):
    wf = session.get(Workflow, workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    old_code = wf.definition_code or ""
    current_revision = compute_code_revision(old_code)
    if payload.base_revision != current_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "revision_mismatch",
                "message": localized_text('hardcoded.api_endpoints_workflows_b4216eec'),
                "current_revision": current_revision,
            },
        )

    try:
        execution = execute_patch_with_validation(old_code, payload.patch_ops, session=session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    new_code = execution.new_code
    changed_nodes = execution.changed_nodes
    applied_ops = execution.applied_ops
    parse_result = execution.parse_result
    validation = execution.validation
    diff = execution.diff

    if payload.dry_run:
        return WorkflowPatchResponse(
            success=bool(parse_result.get("ok")) and bool(validation.get("is_valid")),
            workflow_id=workflow_id,
            base_revision=current_revision,
            new_revision=compute_code_revision(new_code),
            applied_ops=applied_ops,
            changed_nodes=changed_nodes,
            diff=diff,
            new_code=new_code,
            parse_result=parse_result,
            validation=validation,
            error=parse_result.get("error") if not parse_result.get("ok") else None,
        )

    if not parse_result.get("ok"):
        return WorkflowPatchResponse(
            success=False,
            workflow_id=workflow_id,
            base_revision=current_revision,
            applied_ops=applied_ops,
            changed_nodes=changed_nodes,
            diff=diff,
            new_code=new_code,
            parse_result=parse_result,
            validation=validation,
            error=str(parse_result.get("error") or "parse_failed"),
        )

    if not validation.get("is_valid"):
        return WorkflowPatchResponse(
            success=False,
            workflow_id=workflow_id,
            base_revision=current_revision,
            applied_ops=applied_ops,
            changed_nodes=changed_nodes,
            diff=diff,
            new_code=new_code,
            parse_result=parse_result,
            validation=validation,
            error="validate_failed",
        )

    wf.definition_code = new_code
    wf.updated_at = datetime.utcnow()
    session.add(wf)
    session.commit()
    session.refresh(wf)

    from app.services.workflow.trigger_extractor import sync_triggers_cache

    sync_triggers_cache(wf, session)
    session.commit()

    return WorkflowPatchResponse(
        success=True,
        workflow_id=workflow_id,
        base_revision=current_revision,
        new_revision=compute_code_revision(wf.definition_code or ""),
        applied_ops=applied_ops,
        changed_nodes=changed_nodes,
        diff=diff,
        new_code=wf.definition_code or "",
        parse_result=parse_result,
        validation=validation,
    )
