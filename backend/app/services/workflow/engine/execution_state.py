
from dataclasses import dataclass
from typing import Dict, Any, Set, Optional
from datetime import datetime
from sqlmodel import Session, select
from loguru import logger

from app.db.models import NodeExecutionState


@dataclass
class CheckpointData:
    percent: float
    message: str
    data: Optional[Dict[str, Any]]
    timestamp: datetime


@dataclass
class NodeState:
    node_id: str
    node_type: str
    status: str  # idle, running, success, error, paused
    progress: float
    outputs: Optional[Dict[str, Any]]
    checkpoint: Optional[CheckpointData]
    error: Optional[str]


class ExecutionState:


    def __init__(self, run_id: int):
        self.run_id = run_id
        self.context: Dict[str, Any] = {}
        self.completed_nodes: Set[str] = set()
        self.node_states: Dict[str, NodeState] = {}

    @classmethod
    def load(cls, run_id: int, session: Session) -> 'ExecutionState':
        state = cls(run_id)

        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == run_id
        )
        db_states = session.exec(stmt).all()

        if not db_states:
            return state


        for db_state in db_states:
            checkpoint = None
            if db_state.checkpoint_json:
                checkpoint = CheckpointData(
                    percent=db_state.checkpoint_json.get('percent', 0.0),
                    message=db_state.checkpoint_json.get('message', ''),
                    data=db_state.checkpoint_json.get('data'),
                    timestamp=datetime.fromisoformat(
                        db_state.checkpoint_json.get('timestamp', datetime.utcnow().isoformat())
                    )
                )

            node_state = NodeState(
                node_id=db_state.node_id,
                node_type=db_state.node_type,
                status=db_state.status,
                progress=db_state.progress or 0.0,
                outputs=db_state.outputs_json,
                checkpoint=checkpoint,
                error=db_state.error_message
            )

            state.node_states[db_state.node_id] = node_state

            logger.info(
                f"[ExecutionState] \u52a0\u8f7d\u8282\u70b9: {db_state.node_id}, "
                f"status={db_state.status}, "
                f"has_outputs={db_state.outputs_json is not None}, "
                f"outputs_keys={list(db_state.outputs_json.keys()) if db_state.outputs_json else []}"
            )

            if db_state.status in ("success", "skipped"):
                state.completed_nodes.add(db_state.node_id)
                if db_state.outputs_json:
                    state.context[db_state.node_id] = db_state.outputs_json
                    logger.info(
                        f"[ExecutionState] ✅ \u6062\u590d\u8282\u70b9\u8f93\u51fa\u5230\u4e0a\u4e0b\u6587: {db_state.node_id} "
                        f"(status={db_state.status}, outputs={db_state.outputs_json})"
                    )
                else:
                    logger.warning(
                        f"[ExecutionState] ⚠️ \u8282\u70b9\u72b6\u6001\u4e3a {db_state.status} \u4f46 outputs_json \u4e3a None: {db_state.node_id}"
                    )

        logger.info(
            f"[ExecutionState] \u72b6\u6001\u52a0\u8f7d\u5b8c\u6210: run_id={run_id}, "
            f"\u5df2\u5b8c\u6210={len(state.completed_nodes)}\u4e2a\u8282\u70b9, "
            f"\u4e0a\u4e0b\u6587\u53d8\u91cf={list(state.context.keys())}"
        )

        return state

    def save(self, session: Session):
        if not self.node_states:
            return

        for node_id, node_state in self.node_states.items():
            stmt = select(NodeExecutionState).where(
                NodeExecutionState.run_id == self.run_id,
                NodeExecutionState.node_id == node_id
            )
            db_state = session.exec(stmt).first()

            if not db_state:
                db_state = NodeExecutionState(
                    run_id=self.run_id,
                    node_id=node_id,
                    node_type=node_state.node_type
                )

            db_state.status = node_state.status
            db_state.progress = node_state.progress
            db_state.outputs_json = node_state.outputs
            db_state.error_message = node_state.error
            db_state.updated_at = datetime.utcnow()

            if node_state.status == "running" and not db_state.start_time:
                db_state.start_time = datetime.utcnow()
            elif node_state.status in ("success", "error", "paused"):
                if not db_state.end_time:
                    db_state.end_time = datetime.utcnow()

            if node_state.checkpoint:
                db_state.checkpoint_json = {
                    'percent': node_state.checkpoint.percent,
                    'message': node_state.checkpoint.message,
                    'data': node_state.checkpoint.data,
                    'timestamp': node_state.checkpoint.timestamp.isoformat()
                }

            session.add(db_state)

        session.commit()

    def get_node_state(self, node_id: str) -> Optional[NodeState]:
        return self.node_states.get(node_id)

    def update_node_state(
        self,
        node_id: str,
        node_type: str,
        status: str,
        progress: float = 0.0,
        outputs: Optional[Dict[str, Any]] = None,
        checkpoint: Optional[CheckpointData] = None,
        error: Optional[str] = None
    ):
        if node_id not in self.node_states:
            self.node_states[node_id] = NodeState(
                node_id=node_id,
                node_type=node_type,
                status=status,
                progress=progress,
                outputs=outputs,
                checkpoint=checkpoint,
                error=error
            )
        else:
            node_state = self.node_states[node_id]
            node_state.status = status
            node_state.progress = progress
            if outputs is not None:
                node_state.outputs = outputs
            if checkpoint is not None:
                node_state.checkpoint = checkpoint
            if error is not None:
                node_state.error = error

        if status == "success":
            self.completed_nodes.add(node_id)
            if outputs:
                self.context[node_id] = outputs

    def is_completed(self, node_id: str) -> bool:
        return node_id in self.completed_nodes

    def get_checkpoint(self, node_id: str) -> Optional[CheckpointData]:
        node_state = self.node_states.get(node_id)
        return node_state.checkpoint if node_state else None

    def clear_node_states(self, session: Session):
        stmt = select(NodeExecutionState).where(
            NodeExecutionState.run_id == self.run_id
        )
        old_states = session.exec(stmt).all()

        for state in old_states:
            session.delete(state)

        if old_states:
            session.commit()

        self.node_states.clear()
        self.completed_nodes.clear()
        self.context.clear()
