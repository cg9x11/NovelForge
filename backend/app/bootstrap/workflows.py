
from app.locales import localized_text
import os
from sqlmodel import Session, select
from loguru import logger

from app.db.models import Workflow
from app.core.config import settings
from .registry import initializer


def _parse_code_workflow(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    name = os.path.splitext(os.path.basename(file_path))[0]
    description = localized_text('hardcoded.bootstrap_workflows_187cbd50', name=name)

    return {
        "name": name,
        "description": description,
        "code": code,
        "keep_run_history": False,
    }


def _create_or_update_workflow(session: Session, name: str, description: str,
                               code: str, keep_run_history: bool,
                               overwrite: bool) -> tuple[int, int, int]:
    created_count = updated_count = skipped_count = 0

    wf = session.exec(select(Workflow).where(Workflow.name == name)).first()
    if not wf:
        wf = Workflow(
            name=name,
            description=description,
            is_built_in=True,
            is_active=True,
            dsl_version=2,
            definition_code=code,
            keep_run_history=keep_run_history
        )
        session.add(wf)
        session.commit()
        session.refresh(wf)
        created_count += 1
    else:
        if overwrite:
            wf.definition_code = code
            wf.description = description
            wf.is_built_in = True
            wf.is_active = True
            wf.dsl_version = 2
            wf.keep_run_history = keep_run_history
            session.add(wf)
            session.commit()
            updated_count += 1
        else:
            skipped_count += 1

    from app.services.workflow.trigger_extractor import sync_triggers_cache
    sync_triggers_cache(wf, session)
    session.commit()

    return created_count, updated_count, skipped_count


def get_all_workflow_files() -> dict:
    workflow_dir = os.path.join(os.path.dirname(__file__), 'workflows')
    if not os.path.exists(workflow_dir):
        logger.warning(f"Workflow directory not found at {workflow_dir}. Cannot load workflows.")
        return {}

    workflow_files = {}
    for filename in os.listdir(workflow_dir):
        if filename.endswith('.wf'):
            file_path = os.path.join(workflow_dir, filename)
            try:
                workflow_data = _parse_code_workflow(file_path)
                name = workflow_data["name"]
                workflow_files[name] = workflow_data
            except Exception as e:
                logger.error(f"Failed to parse workflow file {filename}: {e}")
                import traceback
                traceback.print_exc()
                continue

    return workflow_files

@initializer(name=localized_text('hardcoded.bootstrap_workflows_cc19798b'), order=50)
def init_workflows(session: Session) -> None:
    overwrite = settings.bootstrap.should_overwrite
    total_created = total_updated = total_skipped = 0

    all_workflows = get_all_workflow_files()

    if not all_workflows:
        return

    for name, workflow_data in all_workflows.items():
        try:
            c, u, s = _create_or_update_workflow(
                session,
                name=workflow_data["name"],
                description=workflow_data["description"],
                code=workflow_data["code"],
                keep_run_history=workflow_data.get("keep_run_history", False),
                overwrite=overwrite
            )
            total_created += c
            total_updated += u
            total_skipped += s
        except Exception as e:
            import traceback
            traceback.print_exc()
            continue

    if total_created > 0 or total_updated > 0:
        pass
    else:
        pass
