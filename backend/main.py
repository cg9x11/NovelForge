import os, sys
from dotenv import load_dotenv

def _load_env_from_nearby():
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, ".env"))
    backend_dir = os.path.abspath(os.path.dirname(__file__))
    candidates.append(os.path.join(backend_dir, ".env"))
    candidates.append(os.path.join(os.getcwd(), ".env"))
    for p in candidates:
        try:
            if os.path.isfile(p):
                load_dotenv(p, override=False)
        except Exception:
            pass

_load_env_from_nearby()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.core import settings
from app.core.startup import startup, shutdown


# Internal note.
@asynccontextmanager
async def lifespan(app):
    # Internal note.
    startup()
    
    # Internal note.
    try:
        from app.db.session import engine
        from sqlmodel import Session
        from app.services.workflow.cleanup import cleanup_expired_runs
        
        with Session(engine) as session:
            cleanup_expired_runs(session)
    except Exception as e:
        print(f"Startup cleanup failed: {e}")
        
    yield
    # Internal note.
    shutdown()

# Internal note.
app = FastAPI(
    title=f"{settings.app.app_name} API",
    version=settings.app.app_version,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Internal note.
from app.core.middleware.workflow import WorkflowHeaderMiddleware
app.add_middleware(WorkflowHeaderMiddleware)

# Internal note.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Workflows-Started"],
)

# Internal note.
app.include_router(api_router, prefix=settings.app.api_prefix)


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.app.app_name} API",
        "version": settings.app.app_version
    }

if __name__ == "__main__":
    import uvicorn

    reload_enabled = os.getenv("NOVELFORGE_BACKEND_RELOAD", "0").lower() in {"1", "true", "yes"}
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=54321,
        reload=reload_enabled,
        timeout_graceful_shutdown=1,
    )
