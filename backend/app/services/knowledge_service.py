from app.locales import localized_text
from typing import List, Optional
from sqlmodel import Session, select
from app.db.models import Knowledge
from app.services.builtin_key_registry import KNOWLEDGE_NAME_TO_KEY, resolve_builtin_key

class KnowledgeService:


    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, skip: int = 0, limit: int = 200) -> List[Knowledge]:
        return self.db.exec(select(Knowledge).offset(skip).limit(limit)).all()

    def get_by_id(self, kid: int) -> Optional[Knowledge]:
        return self.db.get(Knowledge, kid)

    def get_by_name(self, name: str) -> Optional[Knowledge]:
        item = self.db.exec(select(Knowledge).where(Knowledge.name == name)).first()
        if item:
            return item
        resolved = resolve_builtin_key(name, KNOWLEDGE_NAME_TO_KEY)
        if resolved and resolved != name:
            return self.get_by_key(resolved)
        return None

    def get_by_key(self, key: str) -> Optional[Knowledge]:
        return self.db.exec(select(Knowledge).where(Knowledge.key == key)).first()

    def get_by_identifier(self, identifier: str) -> Optional[Knowledge]:
        item = self.get_by_key(identifier)
        if item:
            return item
        return self.get_by_name(identifier)

    def create(self, name: str, content: str, description: Optional[str] = None, built_in: bool = False, key: Optional[str] = None) -> Knowledge:
        kb = Knowledge(key=key or resolve_builtin_key(name, KNOWLEDGE_NAME_TO_KEY), name=name, content=content, description=description, built_in=built_in)
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def update(self, kid: int, name: Optional[str] = None, content: Optional[str] = None, description: Optional[str] = None, key: Optional[str] = None) -> Optional[Knowledge]:
        kb = self.get_by_id(kid)
        if not kb:
            return None
        if key is not None:
            kb.key = key
        if name is not None:
            kb.name = name
        if not getattr(kb, "key", None) and kb.name:
            kb.key = resolve_builtin_key(kb.name, KNOWLEDGE_NAME_TO_KEY)
        if description is not None:
            kb.description = description
        if content is not None:
            kb.content = content
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete(self, kid: int) -> bool:
        kb = self.get_by_id(kid)
        if not kb:
            return False
        if getattr(kb, 'built_in', False):
            raise ValueError(localized_text('hardcoded.services_knowledge_service_2d8b3f24'))
        self.db.delete(kb)
        self.db.commit()
        return True
