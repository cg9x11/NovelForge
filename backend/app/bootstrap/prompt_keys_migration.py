"""Normalize legacy prompt identifiers in persisted JSON payloads.

This initializer is idempotent and safe to run on every startup.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from loguru import logger
from sqlmodel import Session, select

from app.db.models import Card, CardType
from app.services.prompt_service import resolve_prompt_key
from .registry import initializer


def _normalize_prompt_name_field(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    if not isinstance(payload, dict):
        return payload, False
    if not payload.get("prompt_name"):
        return payload, False
    normalized = {**payload}
    prompt_name = str(normalized.get("prompt_name"))
    resolved = resolve_prompt_key(prompt_name)
    if resolved == prompt_name:
        return payload, False
    normalized["prompt_name"] = resolved
    return normalized, True


@initializer(name="PromptKey migration", order=15)
def migrate_prompt_keys(session: Session) -> None:
    changed_card_types = 0
    changed_cards = 0
    changed_review_cards = 0

    card_types = session.exec(select(CardType)).all()
    for card_type in card_types:
        ai_params = getattr(card_type, "ai_params", None)
        if not isinstance(ai_params, dict):
            continue
        normalized, changed = _normalize_prompt_name_field(ai_params)
        if changed:
            card_type.ai_params = normalized
            session.add(card_type)
            changed_card_types += 1

    cards = session.exec(select(Card)).all()
    for card in cards:
        ai_params = getattr(card, "ai_params", None)
        if isinstance(ai_params, dict):
            normalized_ai, changed_ai = _normalize_prompt_name_field(ai_params)
            if changed_ai:
                card.ai_params = normalized_ai
                session.add(card)
                changed_cards += 1

        content = getattr(card, "content", None)
        if not isinstance(content, dict):
            continue
        review = content.get("review_result")
        if not isinstance(review, dict):
            continue
        normalized_review, changed_review = _normalize_prompt_name_field(review)
        if changed_review:
            new_content = {**content, "review_result": normalized_review}
            card.content = new_content
            session.add(card)
            changed_review_cards += 1

    total_changed = changed_card_types + changed_cards + changed_review_cards
    if total_changed:
        session.commit()
        logger.info(
            "[PromptKey migration] normalized prompt_name in "
            f"card_types={changed_card_types}, cards={changed_cards}, review_cards={changed_review_cards}"
        )
    else:
        logger.info("[PromptKey migration] no legacy prompt_name found")

