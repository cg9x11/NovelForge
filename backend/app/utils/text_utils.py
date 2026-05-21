

from app.locales import localized_text
def truncate_text(text: str, limit: int, suffix: str = localized_text('hardcoded.utils_text_utils_5cfddb12')) -> str:
    if len(text) <= limit:
        return text
    truncate_at = max(0, limit - len(suffix))
    return text[:truncate_at] + suffix
