from datetime import datetime, timedelta
from sqlmodel import Session, select, delete
from loguru import logger
from app.db.models import WorkflowRun, Workflow
from app.core.config import settings

def cleanup_expired_runs(session: Session):
    persistent_retention_days = settings.workflow.retention_persistent_days

    now = datetime.utcnow()
    deleted_count = 0

    try:
        stmt_transient = (
            select(WorkflowRun.id)
            .join(Workflow)
            .where(
                WorkflowRun.status.in_(["succeeded", "failed", "cancelled", "timeout"]),
                (Workflow.keep_run_history == False) | (Workflow.keep_run_history == None)
            )
        )
        transient_ids = session.exec(stmt_transient).all()

        if transient_ids:
            stmt_del = delete(WorkflowRun).where(WorkflowRun.id.in_(transient_ids))
            result = session.exec(stmt_del)
            deleted_count += result.rowcount if hasattr(result, 'rowcount') else len(transient_ids)

        persistent_cutoff = now - timedelta(days=persistent_retention_days)
        stmt_persistent = (
            select(WorkflowRun.id)
            .join(Workflow)
            .where(
                WorkflowRun.status.in_(["succeeded", "failed", "cancelled", "timeout"]),
                WorkflowRun.finished_at < persistent_cutoff,
                Workflow.keep_run_history == True
            )
        )
        persistent_ids = session.exec(stmt_persistent).all()

        if persistent_ids:
            stmt_del = delete(WorkflowRun).where(WorkflowRun.id.in_(persistent_ids))
            result = session.exec(stmt_del)
            count = result.rowcount if hasattr(result, 'rowcount') else len(persistent_ids)
            deleted_count += count

        session.commit()
        if deleted_count > 0:


            pass
    except Exception as e:
        session.rollback()
