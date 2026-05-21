
from typing import Dict, Any
from sqlmodel import Session
from app.db.models import Card, LLMConfig
from loguru import logger


def merge_effective_ai_params(session: Session, card: Card) -> Dict[str, Any]:
    base = (card.card_type.ai_params if card.card_type and card.card_type.ai_params else {}) or {}

    override = (card.ai_params or {})

    effective = {**base, **override}

    if effective.get("llm_config_id") in (None, 0, "0", ""):
        try:
            llm = session.query(LLMConfig).order_by(LLMConfig.id.asc()).first()  # type: ignore
            if llm:
                effective["llm_config_id"] = int(getattr(llm, "id", 0))
        except Exception as e:


            pass
    pass
    if effective.get("llm_config_id") is not None:
        try:
            effective["llm_config_id"] = int(effective.get("llm_config_id"))
        except (ValueError, TypeError):
            pass

    return effective
