
from typing import Any, Optional, List, Dict
import re
from sqlmodel import Session
from loguru import logger

from app.db.models import Card


def parse_schema_fields(schema: dict, path: str = "$.content", max_depth: int = 5) -> List[dict]:
    if max_depth <= 0:
        return []

    fields = []
    try:
        defs = schema.get("$defs", {})

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return fields

        for field_name, field_schema in properties.items():
            if not isinstance(field_schema, dict):
                continue

            resolved_schema = resolve_schema_ref(field_schema, defs)

            field_type = resolved_schema.get("type", "unknown")
            field_title = resolved_schema.get("title", field_name)
            field_description = resolved_schema.get("description", "")
            field_path = f"{path}.{field_name}"

            field_info = {
                "name": field_name,
                "title": field_title,
                "type": field_type,
                "path": field_path,
                "description": field_description,
                "required": field_name in schema.get("required", []),
                "expanded": False
            }

            if "anyOf" in resolved_schema:
                non_null_schema = None
                for any_schema in resolved_schema["anyOf"]:
                    if isinstance(any_schema, dict) and any_schema.get("type") != "null":
                        non_null_schema = resolve_schema_ref(any_schema, defs)
                        break
                if non_null_schema:
                    resolved_schema = non_null_schema
                    field_type = resolved_schema.get("type", "unknown")
                    field_info["type"] = field_type

            if field_type == "object" and "properties" in resolved_schema:
                children = parse_schema_fields(resolved_schema, field_path, max_depth - 1)
                if children:
                    field_info["children"] = children
                    field_info["expandable"] = True

            elif field_type == "array" and "items" in resolved_schema:
                items_schema = resolved_schema["items"]
                items_resolved = resolve_schema_ref(items_schema, defs)

                if items_resolved.get("type") == "object" and "properties" in items_resolved:
                    children = parse_schema_fields(items_resolved, f"{field_path}[0]", max_depth - 1)
                    if children:
                        field_info["children"] = children
                        field_info["expandable"] = True
                        field_info["array_item_type"] = "object"
                else:
                    field_info["array_item_type"] = items_resolved.get("type", "unknown")

            fields.append(field_info)

    except Exception as e:
        logger.warning(f"Failed to parse schema field: {e}")

    return fields


def resolve_schema_ref(schema: dict, defs: dict) -> dict:
    if not isinstance(schema, dict):
        return schema

    if "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path.startswith("#/$defs/"):
            ref_name = ref_path.replace("#/$defs/", "")
            if ref_name in defs:
                resolved = defs[ref_name]
                if "title" in schema:
                    resolved = {**resolved, "title": schema["title"]}
                if "description" in schema:
                    resolved = {**resolved, "description": schema["description"]}
                return resolved

    return schema


def get_card_by_id(session: Session, card_id: int) -> Optional[Card]:
    try:
        return session.get(Card, int(card_id))
    except Exception:
        return None


def get_by_path(obj: Any, path: str) -> Any:
    if not path or not isinstance(path, str):
        return None
    if not path.startswith("$."):
        return None
    parts = path[2:].split(".")
    if isinstance(obj, dict) and "$" in obj:
        cur: Any = obj.get("$")
    else:
        cur = obj
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            try:
                cur = getattr(cur, p)
            except Exception:
                return None
    return cur


def set_by_path(obj: Dict[str, Any], path: str, value: Any) -> bool:
    if not isinstance(obj, dict) or not isinstance(path, str) or not path.startswith("$."):
        return False

    parts = path[2:].split(".")
    cur: Dict[str, Any] = obj

    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]  # type: ignore[assignment]

    cur[parts[-1]] = value
    return True


_TPL_PATTERN = re.compile(r"\{([^{}]+)\}")


def resolve_expr(expr: str, state: dict) -> Any:
    expr = expr.strip()
    if expr == "index":
        return (state.get("item") or {}).get("index")
    # item.xxx
    if expr.startswith("item."):
        item = state.get("item") or {}
        return get_by_path({"item": item}, "$." + expr)
    # current.xxx / current.card.xxx
    if expr.startswith("current."):
        cur = state.get("current") or {}
        return get_by_path({"current": cur}, "$." + expr)
    # scope.xxx
    if expr.startswith("scope."):
        scope = state.get("scope") or {}
        return get_by_path({"scope": scope}, "$." + expr)
    if expr.startswith("$."):
        card = (state.get("current") or {}).get("card") or state.get("card")
        base = {"content": getattr(card, "content", {})} if card else {}
        return get_by_path({"$": base}, expr)
    return None


def to_name(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, dict):
        for key in ("name", "title", "label", "content"):
            v = x.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, dict):
                nn = v.get("name") or v.get("title")
                if isinstance(nn, str) and nn.strip():
                    return nn.strip()
    return str(x).strip()


def to_name_list(seq: Any) -> List[str]:
    if not isinstance(seq, list):
        return []
    out: List[str] = []
    for it in seq:
        name = to_name(it)
        if name:
            out.append(name)
    seen = set()
    unique: List[str] = []
    for n in out:
        if n not in seen:
            unique.append(n)
            seen.add(n)
    return unique


def render_value(val: Any, state: dict) -> Any:
    if isinstance(val, dict):
        if "$toNameList" in val and isinstance(val.get("$toNameList"), str):
            seq = resolve_expr(val["$toNameList"], state)
            return to_name_list(seq)
        return {k: render_value(v, state) for k, v in val.items()}
    if isinstance(val, list):
        return [render_value(v, state) for v in val]
    if isinstance(val, str):
        m = _TPL_PATTERN.fullmatch(val.strip())
        if m:
            resolved = resolve_expr(m.group(1), state)
            return resolved
        def repl(match: re.Match) -> str:
            expr = match.group(1)
            res = resolve_expr(expr, state)
            if isinstance(res, (dict, list)):
                return str(res)
            return "" if res is None else str(res)
        return _TPL_PATTERN.sub(repl, val)
    return val


def get_from_state(path_expr: Any, state: dict) -> Any:
    if isinstance(path_expr, str):
        p = path_expr.strip()
        if p in ("item", "$item"):
            return state.get("item")
        if p in ("current", "$current"):
            return state.get("current")
        if p in ("scope", "$scope"):
            return state.get("scope")
        if p.startswith("$item."):
            return resolve_expr("item." + p[len("$item."):], state)
        if p.startswith("$current."):
            return resolve_expr("current." + p[len("$current."):], state)
        if p.startswith("$scope."):
            return resolve_expr("scope." + p[len("$scope."):], state)
        if p.startswith(("item.", "current.", "scope.", "$.")):
            return resolve_expr(p, state)
    return path_expr
