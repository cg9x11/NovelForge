
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict


_HELPER_REGISTRY: Dict[str, Callable[..., Any]] = {}
_HELPER_META_REGISTRY: Dict[str, "HelperMeta"] = {}


@dataclass(frozen=True)
class HelperMeta:


    summary: str
    scenario: str
    priority: int = 50
    example: str = ""


def register_function(
    name: str,
    *,
    summary: str = "",
    scenario: str = "",
    priority: int = 50,
    example: str = "",
):

    def decorator(func: Callable[..., Any]):
        _HELPER_REGISTRY[name] = func
        _HELPER_META_REGISTRY[name] = HelperMeta(
            summary=summary or ((func.__doc__ or "").strip()),
            scenario=scenario or "General",
            priority=priority,
            example=example,
        )
        return func

    return decorator


def get_builtin_functions() -> Dict[str, Callable[..., Any]]:
    return _HELPER_REGISTRY.copy()


def get_helper_metadata() -> Dict[str, HelperMeta]:
    return _HELPER_META_REGISTRY.copy()


@register_function(
    "default",
    summary="General",
    scenario="General",
    priority=75,
    example="General",
)
def fn_default(value: Any, default_value: Any) -> Any:
    return value if value is not None else default_value


@register_function(
    "coalesce",
    summary="General",
    scenario="General",
    priority=85,
    example="General",
)
def fn_coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


@register_function(
    "merge",
    summary="General",
    scenario="General",
    priority=80,
    example="merge(base, {'project_id': project.id})",
)
def fn_merge(*dicts: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for item in dicts:
        if isinstance(item, dict):
            result.update(item)
    return result


@register_function(
    "json_parse",
    summary="General",
    scenario="General",
    priority=60,
    example="json_parse(raw_json).get('items', [])",
)
def fn_json_parse(json_str: str) -> Any:
    return json.loads(json_str)


@register_function(
    "json_stringify",
    summary="General",
    scenario="General",
    priority=55,
    example="json_stringify(result, indent=2)",
)
def fn_json_stringify(obj: Any, indent: int | None = None) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=False)


@register_function(
    "read_file",
    summary="General",
    scenario="General",
    priority=95,
    example="read_file(item.meta.path)",
)
def fn_read_file(path: str, encoding: str = "utf-8") -> str:
    try:
        with open(path, "r", encoding=encoding) as file:
            return file.read()
    except Exception as exc:
        return f"[\u8bfb\u53d6\u5931\u8d25: {exc}]"


@register_function(
    "normalize_ranges",
    summary="General",
    scenario="General",
    priority=92,
    example="normalize_ranges(stages, start=1, end=total_chapters)",
)
def fn_normalize_ranges(
    ranges: Any,
    *,
    start: int = 1,
    end: int | None = None,
    start_key: str = "chapter_start",
    end_key: str = "chapter_end",
) -> list[dict[str, Any]]:

    if not isinstance(ranges, list) or not ranges:
        return []

    normalized: list[dict[str, Any]] = []

    def _to_int(value: Any) -> int | None:
        try:
            return int(value)
        except Exception:
            return None

    cleaned: list[dict[str, Any]] = []
    for item in ranges:
        if not isinstance(item, dict):
            continue
        s = _to_int(item.get(start_key))
        e = _to_int(item.get(end_key))
        if s is None or e is None:
            continue
        copied = dict(item)
        copied[start_key] = s
        copied[end_key] = e
        cleaned.append(copied)

    if not cleaned:
        return []

    cleaned.sort(key=lambda x: (x[start_key], x[end_key]))

    for idx, item in enumerate(cleaned):
        cur = dict(item)
        cur_start = cur[start_key]
        cur_end = cur[end_key]

        if idx == 0:
            if cur_start > start:
                cur_start = start
            if cur_end < cur_start:
                cur_end = cur_start
            if end is not None and cur_end > end:
                cur_end = end
            cur[start_key] = cur_start
            cur[end_key] = cur_end
            normalized.append(cur)
            continue

        prev = normalized[-1]
        prev_end = int(prev[end_key])
        expected = prev_end + 1

        if cur_start > expected:
            prev[end_key] = cur_start - 1
            prev_end = int(prev[end_key])
            expected = prev_end + 1

        if cur_start < expected:
            cur_start = expected

        if cur_end < cur_start:
            cur_end = cur_start

        if end is not None and cur_start > end:
            break

        if end is not None and cur_end > end:
            cur_end = end

        cur[start_key] = cur_start
        cur[end_key] = cur_end
        normalized.append(cur)

    if end is not None and normalized:
        last = normalized[-1]
        if int(last[end_key]) < end:
            last[end_key] = end

    return normalized


@register_function(
    "squash_adjacent_stages",
    summary="General",
    scenario="General",
    priority=90,
    example="squash_adjacent_stages(stages)",
)
def fn_squash_adjacent_stages(
    stages: Any,
    *,
    name_key: str = "stage_name",
    start_key: str = "chapter_start",
    end_key: str = "chapter_end",
    outline_key: str = "stage_outline",
    summary_key: str = "stage_summary",
    tiny_threshold: int = 1,
) -> list[dict[str, Any]]:

    if not isinstance(stages, list) or not stages:
        return []

    def _to_int(value: Any) -> int | None:
        try:
            return int(value)
        except Exception:
            return None

    def _clean_text(value: Any) -> str:
        text = str(value or "").strip().lower()
        if not text:
            return ""
        return re.sub(r"\s+", "", text)

    def _is_similar_text(a: Any, b: Any) -> bool:
        ta = _clean_text(a)
        tb = _clean_text(b)
        if not ta or not tb:
            return False
        if ta == tb:
            return True
        short, long = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
        return len(short) >= 24 and short in long

    cleaned: list[dict[str, Any]] = []
    for item in stages:
        if not isinstance(item, dict):
            continue
        copied = dict(item)
        s = _to_int(copied.get(start_key))
        e = _to_int(copied.get(end_key))
        if s is None or e is None:
            continue
        if e < s:
            e = s
        copied[start_key] = s
        copied[end_key] = e
        cleaned.append(copied)

    if not cleaned:
        return []

    cleaned.sort(key=lambda x: (x[start_key], x[end_key]))

    squashed: list[dict[str, Any]] = []
    for cur in cleaned:
        if not squashed:
            squashed.append(cur)
            continue

        prev = squashed[-1]

        prev_name = str(prev.get(name_key) or "").strip()
        cur_name = str(cur.get(name_key) or "").strip()
        same_name = bool(prev_name and cur_name and prev_name == cur_name)

        cur_len = int(cur[end_key]) - int(cur[start_key]) + 1
        tiny_and_similar = cur_len <= tiny_threshold and (
            _is_similar_text(prev.get(outline_key), cur.get(outline_key))
            or _is_similar_text(prev.get(summary_key), cur.get(summary_key))
        )

        if same_name or tiny_and_similar:
            prev[end_key] = max(int(prev[end_key]), int(cur[end_key]))

            prev_outline = str(prev.get(outline_key) or "")
            cur_outline = str(cur.get(outline_key) or "")
            if len(cur_outline) > len(prev_outline):
                prev[outline_key] = cur_outline

            prev_summary = str(prev.get(summary_key) or "")
            cur_summary = str(cur.get(summary_key) or "")
            if len(cur_summary) > len(prev_summary):
                prev[summary_key] = cur_summary
            continue

        squashed.append(cur)

    return squashed
