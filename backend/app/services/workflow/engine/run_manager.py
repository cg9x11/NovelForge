
import asyncio
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from loguru import logger

from app.db.models import Workflow, WorkflowRun
from .state_manager import StateManager
from .runtime import workflow_runtime


class RunManager:


    def __init__(self, session: Session):
        self.session = session
        self.state_manager = StateManager(session)

    def create_run(
        self,
        workflow_id: int,
        trigger_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> WorkflowRun:
        if idempotency_key:
            stmt = select(WorkflowRun).where(
                WorkflowRun.idempotency_key == idempotency_key,
                WorkflowRun.status.in_(["queued", "running"])
            )
            existing = self.session.exec(stmt).first()
            if existing:
                logger.warning(
                    f"[RunManager] \u5e42\u7b49\u952e\u51b2\u7a81，\u4efb\u52a1\u6b63\u5728\u8fd0\u884c: "
                    f"run_id={existing.id}, status={existing.status}"
                )
                return existing

        workflow = self.session.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(f"\u5de5\u4f5c\u6d41\u4e0d\u5b58\u5728: {workflow_id}")

        if not workflow.is_active:
            raise ValueError(f"\u5de5\u4f5c\u6d41\u672a\u6fc0\u6d3b: {workflow_id}")

        from datetime import datetime
        run = WorkflowRun(
            workflow_id=workflow_id,
            definition_version=workflow.dsl_version,
            status="queued",
            scope_json=trigger_data,
            params_json=params,
            idempotency_key=idempotency_key,
            created_at=datetime.now()
        )

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        self.state_manager.clear_node_states(run.id)

        logger.info(
            f"[RunManager] \u521b\u5efa\u8fd0\u884c: run_id={run.id}, "
            f"workflow_id={workflow_id}"
        )

        return run

    async def start_run(
        self,
        run_id: int,
        priority: int = 0
    ) -> None:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"\u8fd0\u884c\u4e0d\u5b58\u5728: {run_id}")

        workflow = self.session.get(Workflow, run.workflow_id)
        if not workflow:
            raise ValueError(f"\u5de5\u4f5c\u6d41\u4e0d\u5b58\u5728: {run.workflow_id}")

        if workflow_runtime.is_active(run_id):
            return

        task = asyncio.create_task(self._execute_run_in_new_session(run_id))
        workflow_runtime.register_task(run_id, task)

    async def _execute_run_in_new_session(self, run_id: int) -> None:
        from app.db.session import engine as db_engine

        session = Session(db_engine)
        try:
            run = session.get(WorkflowRun, run_id)
            if not run:
                return

            workflow = session.get(Workflow, run.workflow_id)
            if not workflow:
                return

            manager = RunManager(session)
            await manager._execute_run(run, workflow)
        finally:
            session.close()

    async def _execute_run(
        self,
        run: WorkflowRun,
        workflow: Workflow
    ) -> None:
        from ..parser.marker_parser import WorkflowParser
        from .async_executor import AsyncExecutor

        run_id = run.id

        try:
            slot_status = await workflow_runtime.acquire_slot(run_id)
            if slot_status == "cancelled":
                self.state_manager.update_run_status(run_id, "cancelled")
                return
            if slot_status == "paused":
                self.state_manager.update_run_status(run_id, "paused")
                return

            self.state_manager.update_run_status(run_id, "running")

            code = workflow.definition_code or ""

            if not code:
                raise ValueError("Workflow run failed")


            parser = WorkflowParser()
            plan = parser.parse(code)


            initial_context = {}

            if run.scope_json:
                initial_context.update(run.scope_json)
            if run.params_json:
                initial_context.update(run.params_json)

            executor = AsyncExecutor(
                session=self.state_manager.session,
                state_manager=self.state_manager,
                run_id=run_id
            )

            workflow_runtime.register_executor(run_id, executor)

            try:
                async for event in executor.execute_stream(plan, initial_context):
                    pass

                if executor.is_paused or workflow_runtime.is_pause_requested(run_id):
                    self.state_manager.update_run_status(run_id, "paused")
                    return

                result_context = executor.context
            finally:
                workflow_runtime.unregister_executor(run_id, executor)

            self.state_manager.update_run_status(
                run_id,
                "succeeded",
                summary_json={
                    "variables": list(result_context.keys()),
                    "outputs": self.state_manager._make_json_serializable(result_context)
                }
            )


        except asyncio.CancelledError:
            self.state_manager.update_run_status(run_id, "cancelled")
            raise
        except Exception as e:
            error_msg = str(e)

            if isinstance(e, asyncio.TimeoutError):
                self.state_manager.update_run_status(run_id, "timeout")
            else:
                self.state_manager.update_run_status(run_id, "failed")
                self.state_manager.save_error(run_id, error_msg)
        finally:
            workflow_runtime.finish_run(
                run_id,
                keep_pause=workflow_runtime.is_pause_requested(run_id)
            )

    async def cancel_run(self, run_id: int) -> bool:
        if workflow_runtime.request_cancel(run_id):
            self.state_manager.update_run_status(run_id, "cancelled")
            return True

        run = self.session.get(WorkflowRun, run_id)
        if run and run.status in {"queued", "running", "paused"}:
            self.state_manager.update_run_status(run_id, "cancelled")
            return True

        return False

    async def pause_run(self, run_id: int) -> bool:
        if workflow_runtime.request_pause(run_id):
            self.state_manager.update_run_status(run_id, "paused")
            return True

        return False

    async def resume_run(self, run_id: int) -> bool:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            return False

        if run.status != "paused":
            return False

        if workflow_runtime.request_resume(run_id):
            self.state_manager.update_run_status(run_id, "running")
            return True
        else:
            workflow = self.session.get(Workflow, run.workflow_id)
            if not workflow:
                return False

            await self.start_run(run_id)
            return True

    def get_run_status(self, run_id: int) -> Optional[Dict[str, Any]]:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            return None

        node_states = self.state_manager.get_all_node_states(run_id)

        return {
            "run_id": run.id,
            "workflow_id": run.workflow_id,
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "error": run.error_json,
            "nodes": [
                {
                    "node_id": ns.node_id,
                    "node_type": ns.node_type,
                    "status": ns.status,
                    "progress": int(ns.progress) if ns.progress is not None else 0,
                    "error": ns.error_message,
                    "outputs_json": ns.outputs_json
                }
                for ns in node_states
            ]
        }
