from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.workflow_context import init_workflow_context, get_triggered_run_ids

class WorkflowHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        init_workflow_context()

        response = await call_next(request)

        run_ids = get_triggered_run_ids()
        if run_ids:
            existing = response.headers.get("X-Workflows-Started")
            if existing:
                new_ids = f"{existing},{','.join(map(str, run_ids))}"
                response.headers["X-Workflows-Started"] = new_ids
            else:
                response.headers["X-Workflows-Started"] = ",".join(map(str, run_ids))

        return response
