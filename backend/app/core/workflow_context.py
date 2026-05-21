from contextvars import ContextVar
from typing import List

_workflow_runs_ctx: ContextVar[List[int]] = ContextVar("workflow_runs_ctx", default=[])

def init_workflow_context():
    _workflow_runs_ctx.set([])

def add_triggered_run_id(run_id: int):
    current_list = _workflow_runs_ctx.get()
    current_list.append(run_id)

def get_triggered_run_ids() -> List[int]:
    return _workflow_runs_ctx.get()

def clear_workflow_context():
    _workflow_runs_ctx.set([])
