"""Knowledge bootstrap.

Loads built-in knowledge files and initializes them into database.
"""

import os
from sqlmodel import Session, select
from loguru import logger

from app.db.models import Knowledge
from app.services.builtin_key_registry import KNOWLEDGE_NAME_TO_KEY, resolve_builtin_key
from app.core.config import settings
from app.locales import locale_section
from .registry import initializer


@initializer(name="knowledge", order=30)
def init_knowledge(session: Session) -> None:
    """Initialize built-in knowledge files from bootstrap/knowledge."""
    knowledge_dir = os.path.join(os.path.dirname(__file__), 'knowledge')
    if not os.path.exists(knowledge_dir):
        logger.warning(f"Knowledge directory not found at {knowledge_dir}. Cannot load knowledge base.")
        return

    knowledge_names = locale_section("knowledge_names")
    existing_items = session.exec(select(Knowledge)).all()
    for item in existing_items:
        mapped_key = KNOWLEDGE_NAME_TO_KEY.get((item.name or '').strip())
        if mapped_key or not getattr(item, "key", None):
            item.key = mapped_key or resolve_builtin_key(item.name, KNOWLEDGE_NAME_TO_KEY)
    existing_by_name = {k.name: k for k in existing_items}
    existing_by_key = {k.key: k for k in existing_items if getattr(k, "key", None)}
    created = 0
    updated = 0
    skipped = 0
    overwrite = settings.bootstrap.should_overwrite

    for filename in os.listdir(knowledge_dir):
        if not filename.lower().endswith(('.txt', '.md')):
            continue
        file_path = os.path.join(knowledge_dir, filename)
        key = os.path.splitext(filename)[0]
        name = knowledge_names.get(key, key)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception:
            continue
        description = f"Preset knowledge: {name}"
        existing = existing_by_key.get(key) or existing_by_name.get(name)
        if existing:
            if overwrite:
                existing.name = name
                existing.key = key
                existing.content = content
                existing.description = description
                existing.built_in = True
                updated += 1
            else:
                if not getattr(existing, "key", None):
                    existing.key = key
                skipped += 1
        else:
            session.add(Knowledge(key=key, name=name, description=description, content=content, built_in=True))
            created += 1

    if created or updated:
        session.commit()
    else:
        pass
