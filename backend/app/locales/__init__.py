from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=8)
def load_locale(locale: str = "vi-VN") -> dict[str, Any]:
    path = Path(__file__).with_name(f"{locale}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def locale_section(section: str, locale: str = "vi-VN") -> dict[str, Any]:
    value = load_locale(locale).get(section, {})
    return value if isinstance(value, dict) else {}


def schema_field_description(field_name: str, locale: str = "vi-VN") -> str:
    descriptions = locale_section("schema_field_descriptions", locale)
    default_text = load_locale(locale).get("schema_text", {}).get("default_description", "Field description")
    return str(descriptions.get(field_name, default_text))


def localized_text(key: str, default: str = "", locale: str = "vi-VN", **kwargs: Any) -> str:
    value: Any = load_locale(locale)
    for part in key.split("."):
        if not isinstance(value, dict):
            value = None
            break
        value = value.get(part)
    text = str(value if value is not None else default)
    return text.format(**kwargs) if kwargs else text


def localized_list(key: str, default: list[str] | None = None, locale: str = "vi-VN") -> list[str]:
    value: Any = load_locale(locale)
    for part in key.split("."):
        if not isinstance(value, dict):
            value = None
            break
        value = value.get(part)
    if isinstance(value, list):
        return [str(item) for item in value]
    return list(default or [])
