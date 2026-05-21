from app.locales import localized_text
from typing import Any

from app.schemas.chapter_review import ReviewRunRequest


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(_to_text(item) for item in value if _to_text(item))
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            rendered = _to_text(item)
            if rendered:
                lines.append(f"{key}: {rendered}")
        return "\n".join(lines)
    return str(value)


def build_review_prompt(request: ReviewRunRequest) -> str:
    parts: list[str] = [
        localized_text('hardcoded.services_review_review_prompt_builders_3ffa5509'),
        localized_text('hardcoded.services_review_review_prompt_builders_9e189a57', request_title=request.title),
        localized_text('hardcoded.services_review_review_prompt_builders_b952203d', request_review_type=request.review_type),
        localized_text('hardcoded.services_review_review_prompt_builders_c3c94ecc', request_review_profile=request.review_profile),
        localized_text('hardcoded.services_review_review_prompt_builders_2b1f7dc0', request_target_field=request.target_field),
    ]

    if request.context_info:
        parts.extend(["", localized_text('hardcoded.services_review_review_prompt_builders_47e3983e'), request.context_info.strip()])
    if request.facts_info:
        parts.extend(["", localized_text('hardcoded.services_review_review_prompt_builders_1db448ce'), request.facts_info.strip()])

    target_text = _to_text(request.target_text)
    parts.extend(["", localized_text('hardcoded.services_review_review_prompt_builders_063e3537'), target_text or localized_text('hardcoded.services_review_review_prompt_builders_22a8a031')])
    return "\n".join(parts)
