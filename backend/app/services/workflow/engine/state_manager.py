
from typing import Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from loguru import logger

from app.db.models import WorkflowRun, NodeExecutionState
from ..types import NodeStatus, RunStatus


class StateManager:


    def __init__(self, session: Session):
        self.session = session


    def update_run_status(
        self,
        run_id: int,
        status: RunStatus,
        **kwargs
    ) -> WorkflowRun:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"\u8fd0\u884c\u4e0d\u5b58\u5728: {run_id}")

        run.status = status

        if status == "running" and not run.started_at:
            run.started_at = datetime.now()
        elif status in ("succeeded", "failed", "cancelled", "timeout"):
            run.finished_at = datetime.now()

        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)

        return run

    def save_run_state(
        self,
        run_id: int,
        state: Dict[str, Any]
    ) -> None:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"\u8fd0\u884c\u4e0d\u5b58\u5728: {run_id}")

        serializable_state = self._make_json_serializable(state)

        run.state_json = serializable_state
        self.session.add(run)
        self.session.commit()

    def _make_json_serializable(self, obj: Any) -> Any:
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj

    def get_run_state(self, run_id: int) -> Optional[Dict[str, Any]]:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            return None
        return run.state_json or {}

    def save_error(
        self,
        run_id: int,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        run = self.session.get(WorkflowRun, run_id)
        if not run:
            return

        run.error_json = {
            "message": error_message,
            "details": error_details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.session.add(run)
        self.session.commit()


    def create_node_state(
        self,
        run_id: int,
        node_id: str,
        node_type: str
    ) -> NodeExecutionState:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if state:
            state.node_type = node_type
            state.status = "idle"
            state.start_time = None
            state.end_time = None
            state.progress = 0
            state.error_message = None
            state.inputs_json = None
            state.outputs_json = None
            state.logs_json = None
            state.updated_at = datetime.utcnow()
        else:
            state = NodeExecutionState(
                run_id=run_id,
                node_id=node_id,
                node_type=node_type,
                status="idle"
            )

        self.session.add(state)
        self.session.commit()
        self.session.refresh(state)
        return state

    def update_node_status(
        self,
        run_id: int,
        node_id: str,
        status: NodeStatus,
        **kwargs
    ) -> Optional[NodeExecutionState]:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if not state:
            logger.warning(
                f"[StateManager] \u8282\u70b9\u72b6\u6001\u8bb0\u5f55\u4e0d\u5b58\u5728: run_id={run_id}, node_id={node_id}"
            )
            return None

        state.status = status
        state.updated_at = datetime.utcnow()

        if status == "running" and not state.start_time:
            state.start_time = datetime.utcnow()
        elif status in ("success", "error", "skipped"):
            state.end_time = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

        self.session.add(state)
        self.session.commit()
        self.session.refresh(state)

        return state

    def save_node_inputs(
        self,
        run_id: int,
        node_id: str,
        inputs: Dict[str, Any]
    ) -> None:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if state:
            state.inputs_json = inputs
            self.session.add(state)
            self.session.commit()

    def save_node_outputs(
        self,
        run_id: int,
        node_id: str,
        outputs: Dict[str, Any]
    ) -> None:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if state:
            state.outputs_json = outputs
            self.session.add(state)
            self.session.commit()

    def add_node_log(
        self,
        run_id: int,
        node_id: str,
        level: str,
        message: str,
        **kwargs
    ) -> None:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if state:
            logs = state.logs_json or []
            logs.append({
                "level": level,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            })
            state.logs_json = logs
            self.session.add(state)
            self.session.commit()

    def get_node_state(
        self,
        run_id: int,
        node_id: str
    ) -> Optional[NodeExecutionState]:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        return self.session.exec(stmt).first()

    def get_all_node_states(self, run_id: int) -> list[NodeExecutionState]:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id
        )
        return list(self.session.exec(stmt).all())

    def clear_node_states(self, run_id: int) -> None:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id
        )
        old_states = self.session.exec(stmt).all()

        for state in old_states:
            self.session.delete(state)

        if old_states:
            self.session.commit()


    def save_checkpoint(
        self,
        run_id: int,
        node_id: str,
        percent: float,
        message: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        if data:
            import json
            data_size = len(json.dumps(data))
            if data_size > 10 * 1024:  # 10KB
                logger.warning(
                    f"[Checkpoint] \u68c0\u67e5\u70b9\u6570\u636e\u8fc7\u5927: {node_id}, "
                    f"\u5927\u5c0f={data_size} bytes, \u5efa\u8bae < 10KB"
                )

        checkpoint_json = {
            "percent": percent,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if not state:
            logger.warning(
                f"[Checkpoint] \u8282\u70b9\u72b6\u6001\u4e0d\u5b58\u5728，\u521b\u5efa\u65b0\u72b6\u6001: run_id={run_id}, node_id={node_id}"
            )
            state = NodeExecutionState(
                run_id=run_id,
                node_id=node_id,
                node_type="unknown",
                status="running",
                progress=percent,
                checkpoint_json=checkpoint_json
            )
            self.session.add(state)
        else:
            state.progress = percent
            state.checkpoint_json = checkpoint_json
            state.updated_at = datetime.utcnow()

        self.session.commit()
        logger.debug(
            f"[Checkpoint] \u4fdd\u5b58: {node_id}, "
            f"\u8fdb\u5ea6={percent}%, \u6d88\u606f={message}"
        )

    def load_checkpoint(
        self,
        run_id: int,
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id,
            NodeExecutionState.node_id == node_id
        )
        state = self.session.exec(stmt).first()

        if state and state.checkpoint_json:
            logger.debug(
                f"[Checkpoint] \u52a0\u8f7d: {node_id}, "
                f"\u8fdb\u5ea6={state.checkpoint_json.get('percent')}%"
            )
            return state.checkpoint_json

        return None
