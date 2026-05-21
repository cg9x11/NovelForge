from app.locales import localized_text
from loguru import logger
from sqlalchemy import UniqueConstraint, inspect, text
from sqlalchemy.schema import CreateColumn
from sqlmodel import Session, select

from app.bootstrap.registry import discover_and_run_initializers
from app.core.events import discover_event_handlers
from app.db.models import SQLModel, Prompt, CardType, Knowledge, Card
from app.db.session import engine
from app.services.workflow.registry import discover_workflow_nodes
from app.services.builtin_key_registry import PROMPT_NAME_TO_KEY, CARD_TYPE_NAME_TO_KEY, KNOWLEDGE_NAME_TO_KEY, resolve_builtin_key


def init_database():
    logger.info("[Startup] Initializing database schema...")
    SQLModel.metadata.create_all(engine)
    _ensure_safe_additive_columns()
    _backfill_builtin_keys()
    logger.info("[Startup] Database schema initialized")


def _column_has_table_level_unique_constraint(column) -> bool:
    table = column.table
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint) and column.name in constraint.columns.keys():
            return True
    return False


def _can_auto_add_column(column) -> tuple[bool, str]:
    if column.primary_key:
        return False, "primary key"
    if column.unique or _column_has_table_level_unique_constraint(column):
        return False, "unique constraint"
    if column.foreign_keys:
        return False, "foreign key"
    if getattr(column, "computed", None) is not None:
        return False, "computed column"
    if not column.nullable and column.server_default is None:
        return False, "not-null without server_default"
    return True, ""


def _ensure_safe_additive_columns():
    added_columns: list[str] = []
    skipped_columns: list[str] = []

    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        preparer = conn.dialect.identifier_preparer

        for table in SQLModel.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            try:
                db_columns = {item["name"] for item in inspector.get_columns(table.name)}
            except Exception:
                logger.exception(f"[Startup] Failed to inspect table schema: {table.name}")
                continue

            missing_columns = [column for column in table.columns if column.name not in db_columns]

            for column in missing_columns:
                allowed, reason = _can_auto_add_column(column)
                display_name = f"{table.name}.{column.name}"

                if not allowed:
                    skipped_columns.append(f"{display_name} ({reason})")
                    continue

                try:
                    column_ddl = str(CreateColumn(column).compile(dialect=conn.dialect))
                    table_name = preparer.format_table(table)
                    conn.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_ddl}")
                    added_columns.append(display_name)
                except Exception as exc:
                    skipped_columns.append(f"{display_name} (add failed: {exc})")
                    logger.exception(f"[Startup] Failed to add missing column: {display_name}")

    if added_columns:
        logger.info(f"[Startup] Added missing columns: {', '.join(added_columns)}")
    else:
        logger.info("[Startup] Schema check complete, no missing columns")

    if skipped_columns:
        logger.warning(f"[Startup] Skipped unsafe or failed columns: {', '.join(skipped_columns)}")


def _backfill_builtin_keys():
    updated: list[str] = []
    with Session(engine) as session:
        specs = [
            (Prompt, PROMPT_NAME_TO_KEY),
            (CardType, CARD_TYPE_NAME_TO_KEY),
            (Knowledge, KNOWLEDGE_NAME_TO_KEY),
        ]
        for model, mapping in specs:
            for row in session.exec(select(model)).all():
                name = getattr(row, "name", None)
                desired = mapping.get((name or "").strip()) or getattr(row, "key", None) or resolve_builtin_key(name, mapping)
                if desired and getattr(row, "key", None) != desired:
                    row.key = desired
                    session.add(row)
                    updated.append(f"{model.__name__}:{name}->{desired}")
        if updated:
            session.commit()
            logger.info(f"[Startup] Backfilled builtin keys: {', '.join(updated[:20])}{' ...' if len(updated) > 20 else ''}")
        else:
            logger.info("[Startup] Builtin keys already up to date")



def _has_cjk(value: str | None) -> bool:
    return any(localized_text('hardcoded.core_startup_d274eee8') <= ch <= localized_text('hardcoded.core_startup_5e62e292') for ch in (value or ""))


def _choose_key_keeper(rows):
    def score(row):
        return (
            0 if not _has_cjk(getattr(row, "name", None)) else 1,
            0 if getattr(row, "built_in", False) else 1,
            getattr(row, "id", 0) or 0,
        )
    return sorted(rows, key=score)[0]


def _copy_missing_builtin_fields(target, source, fields: list[str]) -> None:
    for field in fields:
        current = getattr(target, field, None)
        incoming = getattr(source, field, None)
        if (current is None or current == "" or current == {}) and incoming not in (None, "", {}):
            setattr(target, field, incoming)


def _dedupe_builtin_keys():
    """Merge duplicate built-in rows created before stable keys existed."""
    removed: list[str] = []
    with Session(engine) as session:
        specs = [
            (Prompt, ["description", "template", "version"]),
            (CardType, ["model_name", "description", "json_schema", "ai_params", "editor_component", "default_ai_context_template", "default_ai_context_template_review", "ui_layout"]),
            (Knowledge, ["description", "content"]),
        ]
        for model, merge_fields in specs:
            rows = [row for row in session.exec(select(model)).all() if getattr(row, "key", None)]
            groups: dict[str, list] = {}
            for row in rows:
                groups.setdefault(row.key, []).append(row)

            for key, duplicates in groups.items():
                if len(duplicates) <= 1:
                    continue
                keeper = _choose_key_keeper(duplicates)
                keeper.built_in = any(getattr(row, "built_in", False) for row in duplicates)
                for row in duplicates:
                    if row.id == keeper.id:
                        continue
                    _copy_missing_builtin_fields(keeper, row, merge_fields)
                    if model is CardType:
                        session.exec(
                            text("UPDATE card SET card_type_id = :keeper_id WHERE card_type_id = :old_id"),
                            params={"keeper_id": keeper.id, "old_id": row.id},
                        )
                    session.delete(row)
                    removed.append(f"{model.__name__}:{key}:{row.id}->{keeper.id}")
                session.add(keeper)

        if removed:
            session.commit()
            logger.info(f"[Startup] Removed duplicate builtin key rows: {', '.join(removed[:30])}{' ...' if len(removed) > 30 else ''}")
        else:
            logger.info("[Startup] No duplicate builtin key rows")

def init_application_data():
    logger.info("[Startup] Initializing application data...")
    with Session(engine) as session:
        discover_and_run_initializers(session)
    logger.info("[Startup] Application data initialized")


def register_event_handlers():
    logger.info("[Startup] Registering event handlers...")
    import app.services  # noqa: F401

    discover_event_handlers()
    logger.info("[Startup] Event handlers registered")


def register_workflow_nodes():
    logger.info("[Startup] Registering workflow nodes...")
    discover_workflow_nodes()
    logger.info("[Startup] Workflow nodes registered")


def cleanup_zombie_runs():
    logger.info("[Startup] Cleaning zombie workflow runs...")

    from sqlmodel import select

    from app.db.models import WorkflowRun

    with Session(engine) as session:
        stmt = select(WorkflowRun).where(WorkflowRun.status == "running")
        zombie_runs = session.exec(stmt).all()

        if zombie_runs:
            logger.warning(f"[Startup] Found {len(zombie_runs)} zombie workflow runs, cleaning...")
            for run in zombie_runs:
                run.status = "failed"
                if not run.error_json:
                    run.error_json = {"error": "Server restarted; run interrupted"}
                session.add(run)
                logger.info(f"[Startup] Cleaning zombie run: run_id={run.id}, workflow_id={run.workflow_id}")
            session.commit()
            logger.info(f"[Startup] Cleaned {len(zombie_runs)} zombie workflow runs")
        else:
            logger.info("[Startup] No zombie workflow runs found")

    logger.info("[Startup] Zombie workflow run cleanup complete")


def startup():
    logger.info("=" * 50)
    logger.info("NovelForge backend starting...")
    logger.info("=" * 50)

    init_database()
    init_application_data()
    _backfill_builtin_keys()
    _dedupe_builtin_keys()
    register_event_handlers()
    register_workflow_nodes()
    cleanup_zombie_runs()

    logger.info("=" * 50)
    logger.info("NovelForge backend started")
    logger.info("=" * 50)


def shutdown():
    logger.info("NovelForge backend shutting down...")
    logger.info("NovelForge backend stopped")
