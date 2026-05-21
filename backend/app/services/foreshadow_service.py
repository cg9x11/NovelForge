from __future__ import annotations

from typing import Any, Dict, List, Optional
import re
from sqlmodel import Session, select
from datetime import datetime

from app.db.models import ForeshadowItem as ForeshadowItemModel
from app.locales import localized_list

INTENT_WORDS = localized_list("foreshadow.intent_words")
ITEM_SUFFIXES = localized_list("foreshadow.item_suffixes")
STOPWORDS = set(localized_list("foreshadow.stopwords"))
CJK_NAME_RANGE = localized_list("foreshadow.cjk_name_range")[0]


class ForeshadowService:
    def __init__(self, session: Session):
        self.session = session

    def suggest(self, text: str) -> Dict[str, Any]:
        if not isinstance(text, str):
            text = str(text or "")
        goals: List[str] = []
        items: List[str] = []
        persons: List[str] = []

        for m in re.findall(rf"({'|'.join(map(re.escape, INTENT_WORDS))})([^???\n]{{2,20}})", text):
            frag = (m[0] + m[1]).strip()
            if frag and frag not in goals:
                goals.append(frag)

        for m in re.findall(rf"([{CJK_NAME_RANGE}]{{1,8}})({'|'.join(map(re.escape, ITEM_SUFFIXES))})", text):
            frag = (m[0] + m[1]).strip()
            if frag and frag not in items:
                items.append(frag)

        for m in re.findall(rf"([{CJK_NAME_RANGE}]{{2,4}})", text):
            if m and 2 <= len(m) <= 4 and m not in STOPWORDS:
                if m not in persons:
                    persons.append(m)
        persons = persons[:10]

        return {
            "goals": goals[:8],
            "items": items[:8],
            "persons": persons,
        }

    # --- CRUD via DB ---
    def list(self, project_id: int, status: Optional[str] = None) -> List[ForeshadowItemModel]:
        stmt = select(ForeshadowItemModel).where(ForeshadowItemModel.project_id == project_id)
        if status:
            stmt = stmt.where(ForeshadowItemModel.status == status)
        items = self.session.exec(stmt.order_by(ForeshadowItemModel.status.desc(), ForeshadowItemModel.created_at.desc())).all()
        return items

    def register(self, project_id: int, entries: List[Dict[str, Any]]) -> List[ForeshadowItemModel]:
        out: List[ForeshadowItemModel] = []
        for it in entries:
            title = str(it.get('title') or '').strip()
            if not title:
                continue
            item = ForeshadowItemModel(
                project_id=project_id,
                chapter_id=it.get('chapter_id'),
                title=title,
                type=str(it.get('type') or 'other') or 'other',
                note=it.get('note'),
                status='open',
            )
            self.session.add(item)
            out.append(item)
        if out:
            self.session.commit()
            for i in out:
                self.session.refresh(i)
        return out

    def resolve(self, project_id: int, item_id: str | int) -> Optional[ForeshadowItemModel]:
        item = self.session.get(ForeshadowItemModel, item_id)
        if not item or item.project_id != project_id:
            return None
        if item.status != 'resolved':
            item.status = 'resolved'
            item.resolved_at = datetime.utcnow()
            self.session.add(item)
            self.session.commit()
            self.session.refresh(item)
        return item

    def delete(self, project_id: int, item_id: str | int) -> bool:
        item = self.session.get(ForeshadowItemModel, item_id)
        if not item or item.project_id != project_id:
            return False
        self.session.delete(item)
        self.session.commit()
        return True
