
from typing import Literal, Any, Callable, Dict
from dataclasses import dataclass, field
from datetime import datetime


NodeStatus = Literal["idle", "pending", "running", "success", "error", "skipped"]

RunStatus = Literal["queued", "running", "succeeded", "failed", "cancelled", "paused", "timeout"]

ErrorHandling = Literal["stop", "continue"]

LogLevel = Literal["debug", "info", "warn", "error"]


@dataclass
class NodeMetadata:
    type: str
    category: str
    label: str
    description: str
    documentation: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    executor: Callable


@dataclass
class WorkflowSettings:
    max_execution_time: int | None = None
    timeout: int = 300
    error_handling: ErrorHandling = "stop"
    max_concurrency: int = 5
    log_level: LogLevel = "info"


@dataclass
class ExecutionContext:
    run_id: int
    node_id: str
    node_type: str
    config: dict[str, Any]
    inputs: dict[str, Any]
    variables: dict[str, Any]
    node_outputs: dict[str, dict[str, Any]]
    settings: WorkflowSettings
    session: Any  # SQLModel Session
    checkpoint: dict[str, Any] | None = None
    "Checkpoint data injected by executor during resume."


@dataclass
class ExecutionEvent:
    type: str  # run.started | node.started | node.progress | node.completed | node.error | run.completed | run.paused | run.cancelled
    data: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_sse(self) -> str:
        import json
        return f"event: {self.type}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"

