
import asyncio
from typing import TYPE_CHECKING
from loguru import logger
from sqlmodel import Session

if TYPE_CHECKING:
    from .execution_state import ExecutionState
    from ..engine.execution_plan import Statement
    from .async_executor import ProgressEvent


class ExecutionError(Exception):
    def __init__(self, node_id: str, message: str, details: dict = None):
        self.node_id = node_id
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NodeExecutionError(ExecutionError):
    pass


class CheckpointError(ExecutionError):
    pass


class ErrorHandler:


    @staticmethod
    async def handle_node_error(
        error: Exception,
        stmt: 'Statement',
        execution_state: 'ExecutionState',
        session: Session
    ) -> 'ProgressEvent':
        from .async_executor import ProgressEvent


        execution_state.update_node_state(
            node_id=stmt.variable,
            node_type=stmt.node_type or "unknown",
            status="error",
            error=str(error)
        )

        execution_state.save(session)

        return ProgressEvent(
            statement=stmt,
            type='error',
            error=str(error)
        )

    @staticmethod
    async def handle_cancellation(
        stmt: 'Statement',
        execution_state: 'ExecutionState',
        session: Session
    ):

        node_state = execution_state.get_node_state(stmt.variable)
        current_progress = node_state.progress if node_state else 0.0

        execution_state.update_node_state(
            node_id=stmt.variable,
            node_type=stmt.node_type or "unknown",
            status="paused",
            progress=current_progress
        )

        execution_state.save(session)
