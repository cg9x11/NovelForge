from __future__ import annotations

from typing import Optional
from sqlmodel import Session, select

from app.db.models import CardType
from app.services.builtin_key_registry import CARD_TYPE_NAME_TO_KEY, resolve_builtin_key


def get_card_type_by_name(session: Session, type_name: str) -> Optional[CardType]:
    return session.exec(select(CardType).where(CardType.name == type_name)).first()


def get_card_type_by_key(session: Session, type_key: str) -> Optional[CardType]:
    return session.exec(select(CardType).where(CardType.key == type_key)).first()


def resolve_card_type_key(identifier: str | None) -> str | None:
    return resolve_builtin_key(identifier, CARD_TYPE_NAME_TO_KEY)


def get_card_type_by_identifier(session: Session, identifier: str | None) -> Optional[CardType]:
    if not identifier:
        return None
    card_type = get_card_type_by_key(session, identifier)
    if card_type:
        return card_type
    card_type = get_card_type_by_name(session, identifier)
    if card_type:
        return card_type
    resolved = resolve_card_type_key(identifier)
    if resolved and resolved != identifier:
        return get_card_type_by_key(session, resolved)
    return None
