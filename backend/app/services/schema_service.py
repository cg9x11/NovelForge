
import re
from typing import Dict, Any, Set
from copy import deepcopy
from sqlmodel import Session
from app.db.models import CardType
from app.schemas.entity import DYNAMIC_INFO_TYPES
from app.schemas import entity as entity_schemas
from loguru import logger
from app.locales import locale_section



SCHEMA_FIELD_TITLES: Dict[str, str] = locale_section("schema_field_titles")
SCHEMA_TEXT: Dict[str, str] = locale_section("schema_text")
CONTEXT_TEMPLATE_LABELS: Dict[str, str] = locale_section("context_template_labels")

_CJK_RE = re.compile(f"[{chr(0x4e00)}-{chr(0x9fff)}]")


def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def _derive_title_from_description(description: Any) -> str | None:
    if not isinstance(description, str):
        return None
    desc = description.strip()
    if not desc or not _contains_cjk(desc):
        return None

    candidate = re.split(r"[，。；;！？:：\n（(]", desc, maxsplit=1)[0].strip()
    if not candidate:
        return None
    if len(candidate) > 16:
        candidate = candidate[:16].strip()
    return candidate or None


def localize_schema_titles(schema: Any) -> Any:
    if not isinstance(schema, (dict, list)):
        return schema

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for field_name, field_schema in properties.items():
                    if isinstance(field_schema, dict):
                        current_title = str(field_schema.get("title") or "")
                        localized = SCHEMA_FIELD_TITLES.get(field_name)
                        if localized and (not current_title or _contains_cjk(current_title)):
                            field_schema["title"] = localized
                        elif not current_title:
                            derived = _derive_title_from_description(field_schema.get("description"))
                            if derived:
                                field_schema["title"] = derived

            for defs_key in ("$defs", "definitions"):
                defs = node.get(defs_key)
                if isinstance(defs, dict):
                    for def_schema in defs.values():
                        visit(def_schema)

            items = node.get("items")
            if isinstance(items, dict):
                visit(items)

            prefix_items = node.get("prefixItems")
            if isinstance(prefix_items, list):
                for item in prefix_items:
                    visit(item)

            for union_key in ("anyOf", "oneOf", "allOf"):
                variants = node.get(union_key)
                if isinstance(variants, list):
                    for variant in variants:
                        visit(variant)

            for key, value in list(node.items()):
                if isinstance(value, str) and key in {"title", "description", "default", "example"}:
                    node[key] = SCHEMA_TEXT.get(value, value)
                elif isinstance(value, list) and key == "examples":
                    node[key] = [SCHEMA_TEXT.get(item, item) if isinstance(item, str) else item for item in value]

            for value in node.values():
                if isinstance(value, (dict, list)):
                    visit(value)

        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(schema)
    return schema



def collect_ref_names(node: Any) -> Set[str]:
    names: Set[str] = set()
    if isinstance(node, dict):
        if '$ref' in node and isinstance(node['$ref'], str) and node['$ref'].startswith('#/$defs/'):
            names.add(node['$ref'].split('/')[-1])
        for v in node.values():
            names |= collect_ref_names(v)
    elif isinstance(node, list):
        for it in node:
            names |= collect_ref_names(it)
    return names



_BUILTIN_DEFS_CACHE: Dict[str, Any] | None = None

def get_builtin_defs() -> Dict[str, Any]:
    global _BUILTIN_DEFS_CACHE
    if _BUILTIN_DEFS_CACHE is not None:
        return _BUILTIN_DEFS_CACHE

    from app.schemas.response_registry import RESPONSE_MODEL_MAP

    merged: Dict[str, Any] = {}
    for _, model_class in RESPONSE_MODEL_MAP.items():
        sch = model_class.model_json_schema(ref_template="#/$defs/{model}")
        sch = localize_schema_titles(sch)
        defs = sch.get('$defs') or {}
        merged.update(defs)

    _BUILTIN_DEFS_CACHE = merged
    return merged


def augment_schema_with_builtin_defs(schema: Dict[str, Any]) -> Dict[str, Any]:
    sch = deepcopy(schema) if schema is not None else {}
    if not isinstance(sch, dict):
        return sch

    ref_names = collect_ref_names(sch)
    if not ref_names:
        return localize_schema_titles(sch)

    builtin_defs = get_builtin_defs()

    if '$defs' not in sch:
        sch['$defs'] = {}

    for name in ref_names:
        if name in builtin_defs and name not in sch['$defs']:
            sch['$defs'][name] = builtin_defs[name]

    return localize_schema_titles(sch)



def compose_schema_with_card_types(session: Session, schema: Dict[str, Any]) -> Dict[str, Any]:
    sch = deepcopy(schema) if isinstance(schema, dict) else {}
    if not isinstance(sch, dict):
        return sch

    if '$defs' not in sch:
        sch['$defs'] = {}

    ref_names = collect_ref_names(sch)
    if not ref_names:
        return localize_schema_titles(sch)

    all_types = session.query(CardType).all()
    by_model: Dict[str, Any] = {}

    for ct in all_types:
        if ct and ct.json_schema:
            localized_schema = localize_schema_titles(deepcopy(ct.json_schema))
            if ct.model_name:
                by_model[ct.model_name] = localized_schema
            by_model[ct.name] = localized_schema

    for name in ref_names:
        if name in by_model:
            sch['$defs'][name] = by_model[name]

    return localize_schema_titles(sch)


def compose_full_schema(session: Session, schema: Dict[str, Any]) -> Dict[str, Any]:
    sch = augment_schema_with_builtin_defs(schema)
    sch = compose_schema_with_card_types(session, sch)
    return localize_schema_titles(sch)
