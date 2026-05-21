
from app.locales import localized_text
from app.locales import schema_field_description
from sqlmodel import Session, select
from loguru import logger

from app.db.models import Project
from .registry import initializer


@initializer(name=localized_text('hardcoded.bootstrap_projects_874427b2'), order=40)
def init_reserved_project(session: Session) -> None:
    FREE_NAME = "__free__"
    exists = session.exec(select(Project).where(Project.name == FREE_NAME)).first()
    if not exists:
        p = Project(name=FREE_NAME, description=schema_field_description("default"))
        session.add(p)
        session.commit()
        session.refresh(p)
    else:
        pass
