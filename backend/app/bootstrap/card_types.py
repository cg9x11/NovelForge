from app.locales import schema_field_description
"""Card type bootstrap.

Initializes built-in card types and schema definitions.
"""

import re
from typing import Any, Dict

from sqlmodel import Session, select
from loguru import logger

from app.core.config import settings
from app.db.models import Card, CardType, LLMConfig
from app.services.builtin_key_registry import CARD_TYPE_NAME_TO_KEY, resolve_builtin_key
from app.schemas.response_registry import RESPONSE_MODEL_MAP
from app.locales import locale_section
from .registry import initializer


FIELD_TITLE_ZH_MAP: Dict[str, str] = locale_section("schema_field_titles")
FIELD_DESCRIPTION_VI_MAP: Dict[str, str] = locale_section("schema_field_descriptions")
_DESCRIPTION_PLACEHOLDERS = {"Field description", "Mo ta truong.", "Mo ta truong"}

_CJK_RE = re.compile(f"[{chr(0x4e00)}-{chr(0x9fff)}]")
def _contains_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def _derive_title_from_description(description: Any) -> str | None:
    if not isinstance(description, str):
        return None
    desc = description.strip()
    if not desc or not _contains_cjk(desc):
        return None

    candidate = re.split(r"[,.;:(\n]", desc, maxsplit=1)[0].strip()
    if not candidate:
        return None
    if len(candidate) > 16:
        candidate = candidate[:16].strip()
    return candidate or None


def _localize_schema_titles(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for field_name, field_schema in properties.items():
                    if not isinstance(field_schema, dict):
                        continue
                    current_title = str(field_schema.get("title") or "")
                    localized = FIELD_TITLE_ZH_MAP.get(field_name)
                    default_title = field_name.replace("_", " ").title()
                    if localized and (not current_title or _contains_cjk(current_title) or current_title == default_title):
                        field_schema["title"] = localized
                    elif not current_title:
                        derived = _derive_title_from_description(field_schema.get("description"))
                        if derived:
                            field_schema["title"] = derived
                    current_description = field_schema.get("description")
                    localized_description = FIELD_DESCRIPTION_VI_MAP.get(field_name)
                    if localized_description and (
                        not isinstance(current_description, str)
                        or current_description.strip() in _DESCRIPTION_PLACEHOLDERS
                        or _contains_cjk(current_description)
                    ):
                        field_schema["description"] = localized_description
                    visit(field_schema)

            defs = node.get("$defs")
            if isinstance(defs, dict):
                for def_schema in defs.values():
                    visit(def_schema)

            items = node.get("items")
            if isinstance(items, dict):
                visit(items)

            for union_key in ("anyOf", "oneOf", "allOf"):
                variants = node.get(union_key)
                if isinstance(variants, list):
                    for variant in variants:
                        visit(variant)

        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(schema)
    return schema

@initializer(name="card_types", order=20)
def create_default_card_types(session: Session) -> None:
    """Initialize built-in card types.

    Create built-in card types, schemas, and AI parameter presets.

    Args:
        session: Database session.
    """
    default_types = {
        "general_text": {"editor_component": "MarkdownTextEditor", "is_singleton": False, "is_ai_enabled": False, "default_ai_context_template": None},
        "work_tags": {"editor_component": "TagsEditor", "is_singleton": True, "is_ai_enabled": False, "default_ai_context_template": None},
        "special_ability": {"is_singleton": True, "default_ai_context_template": None},
        "one_sentence": {"is_singleton": True, "default_ai_context_template": None},
        "story_outline": {"is_singleton": True, "default_ai_context_template": None},
        "world_building": {"is_singleton": True, "default_ai_context_template": None},
        "blueprint": {"is_singleton": True, "default_ai_context_template": None},
        "volume_outline": {"default_ai_context_template": None},
        "writing_guide": {"is_singleton": False, "default_ai_context_template": None},
        "stage_outline": {"default_ai_context_template": None, "default_ai_context_template_review": None},
        "chapter_outline": {"default_ai_context_template": None},
        "chapter_body": {"editor_component": "CodeMirrorEditor", "is_ai_enabled": False, "default_ai_context_template": None, "default_ai_context_template_review": None},
        "review_result_card": {"editor_component": "ReviewResultCardEditor", "is_ai_enabled": False, "default_ai_context_template": None, "default_ai_context_template_review": None},
        "character_card": {"default_ai_context_template": None},
        "scene_card": {"default_ai_context_template": None},
        "organization_card": {"default_ai_context_template": None},
        "item_card": {"is_ai_enabled": False, "default_ai_context_template": None},
        "concept_card": {"is_ai_enabled": False, "default_ai_context_template": None},
        "folder": {"is_singleton": False, "is_ai_enabled": False, "default_ai_context_template": None},
    }

    DEFAULT_AI_PARAMS = {
        "special_ability": {"prompt_name": "special_ability_generation", "temperature": 0.6, "max_tokens": 4096, "timeout": 120},
        "one_sentence": {"prompt_name": "one_sentence", "temperature": 0.6, "max_tokens": 4096, "timeout": 120},
        "story_outline": {"prompt_name": "paragraph_outline", "temperature": 0.7, "max_tokens": 8192, "timeout": 120},
        "world_building": {"prompt_name": "world_building", "temperature": 0.7, "max_tokens": 4096, "timeout": 150},
        "blueprint": {"prompt_name": "blueprint", "temperature": 0.7, "max_tokens": 8192, "timeout": 150},
        "volume_outline": {"prompt_name": "volume_outline", "temperature": 0.7, "max_tokens": 8192, "timeout": 150},
        "writing_guide": {"prompt_name": "writing_guide", "temperature": 0.6, "max_tokens": 8192, "timeout": 120},
        "stage_outline": {"prompt_name": "stage_outline", "temperature": 0.7, "max_tokens": 8192, "timeout": 120},
        "chapter_outline": {"prompt_name": "chapter_outline", "temperature": 0.7, "max_tokens": 8192, "timeout": 120},
        "chapter_body": {"prompt_name": "content_generation", "temperature": 0.7, "max_tokens": 8192, "timeout": 120},
        "review_result_card": None,
        "character_card": {"prompt_name": "character_dynamic_info_extraction", "temperature": 0.6, "max_tokens": 4096, "timeout": 120},
        "scene_card": {"prompt_name": "content_generation", "temperature": 0.6, "max_tokens": 4096, "timeout": 120},
        "organization_card": {"prompt_name": "relationship_extraction", "temperature": 0.6, "max_tokens": 4096, "timeout": 120},
        "item_card": None,
        "concept_card": None,
    }

    TYPE_TO_MODEL_KEY = {
        "general_text": "Text",
        "work_tags": "Tags",
        "special_ability": "SpecialAbilityResponse",
        "one_sentence": "OneSentence",
        "story_outline": "ParagraphOverview",
        "world_building": "WorldBuilding",
        "blueprint": "Blueprint",
        "volume_outline": "VolumeOutline",
        "writing_guide": "WritingGuide",
        "stage_outline": "StageLine",
        "chapter_outline": "ChapterOutline",
        "chapter_body": "Chapter",
        "review_result_card": "ReviewResultCardContent",
        "character_card": "CharacterCard",
        "scene_card": "SceneCard",
        "organization_card": "OrganizationCard",
        "item_card": "ItemCard",
        "concept_card": "ConceptCard",
        "folder": "Text",
    }

    card_type_names = locale_section("card_type_names")
    card_context_templates = locale_section("card_context_templates")
    for card_type_key, templates in card_context_templates.items():
        details = default_types.get(card_type_key)
        if not details or not isinstance(templates, dict):
            continue
        details["default_ai_context_template"] = templates.get("generation")
        details["default_ai_context_template_review"] = templates.get("review")
    default_suffix = str(locale_section("common").get("default_suffix", "default"))

    overwrite_card_schemas = settings.bootstrap.should_overwrite_card_schemas

    existing_types = session.exec(select(CardType)).all()
    for existing_type in existing_types:
        mapped_key = CARD_TYPE_NAME_TO_KEY.get((existing_type.name or '').strip())
        if mapped_key or not getattr(existing_type, "key", None):
            existing_type.key = mapped_key or resolve_builtin_key(existing_type.name, CARD_TYPE_NAME_TO_KEY)
    existing_type_by_name = {ct.name: ct for ct in existing_types}
    existing_type_by_key = {ct.key: ct for ct in existing_types if getattr(ct, "key", None)}

    # Default llm_config_id: first available LLM config, if any.
    default_llm = session.exec(select(LLMConfig)).first()

    for card_type_key, details in default_types.items():
        name = card_type_names.get(card_type_key, card_type_key)
        existing_type = existing_type_by_key.get(card_type_key) or existing_type_by_name.get(name)
        if not existing_type:
            # Store json_schema directly on card type.
            schema = None
            try:
                model_class = RESPONSE_MODEL_MAP.get(TYPE_TO_MODEL_KEY.get(card_type_key))
                if model_class:
                    schema = model_class.model_json_schema(ref_template="#/$defs/{model}")
                    schema = _localize_schema_titles(schema)
            except Exception:
                schema = None
            # AI parameter preset; llm_config_id remains user-selectable.
            ai_params = DEFAULT_AI_PARAMS.get(card_type_key)
            if ai_params is not None:
                # Use default LLM id when available; avoid 0 because FE cannot identify it.
                ai_params = {**ai_params, "llm_config_id": (default_llm.id if default_llm else None)}
            card_type = CardType(
                key=card_type_key,
                name=card_type_names.get(card_type_key, name),
                model_name=TYPE_TO_MODEL_KEY.get(card_type_key, card_type_key),
                description=details.get("description", f"{card_type_names.get(card_type_key, name)} {default_suffix}"),
                json_schema=schema,
                ai_params=ai_params,
                editor_component=details.get("editor_component"),
                is_ai_enabled=details.get("is_ai_enabled", True),
                is_singleton=details.get("is_singleton", False),
                default_ai_context_template=details.get("default_ai_context_template"),
                default_ai_context_template_review=details.get("default_ai_context_template_review"),
                built_in=True,
            )
            session.add(card_type)
            logger.info(f"Created default card type: {card_type_key}")
        else:
            # Incremental update: refresh schema and metadata.
            ct = existing_type
            ct.name = card_type_names.get(card_type_key, name)
            ct.key = card_type_key
            try:
                model_class = RESPONSE_MODEL_MAP.get(TYPE_TO_MODEL_KEY.get(card_type_key))
                if model_class:
                    schema = model_class.model_json_schema(ref_template="#/$defs/{model}")
                    schema = _localize_schema_titles(schema)
                    if ct.json_schema is None or overwrite_card_schemas:
                        ct.json_schema = schema
                    else:
                        ct.json_schema = _localize_schema_titles(ct.json_schema)
            except Exception:
                pass
            # Fill missing ai_params from preset without overwriting user settings.
            if getattr(ct, 'ai_params', None) is None:
                preset = DEFAULT_AI_PARAMS.get(card_type_key)
                if preset is not None:
                    ct.ai_params = {**preset, "llm_config_id": (default_llm.id if default_llm else None)}
            # Fill missing model_name from mapping.
            if not getattr(ct, 'model_name', None):
                ct.model_name = TYPE_TO_MODEL_KEY.get(card_type_key, card_type_key)
            ct.editor_component = details.get("editor_component")
            ct.is_ai_enabled = details.get("is_ai_enabled", True)
            ct.is_singleton = details.get("is_singleton", False)
            ct.description = details.get("description", f"{card_type_names.get(card_type_key, name)} {default_suffix}")
            ct.default_ai_context_template = details.get("default_ai_context_template")
            ct.default_ai_context_template_review = details.get("default_ai_context_template_review")
            ct.built_in = True

    session.flush()

    all_cards = session.exec(select(Card)).all()
    for card in all_cards:
        card_type = existing_type_by_key.get(getattr(card.card_type, "key", None)) or existing_type_by_name.get(getattr(card.card_type, "name", ""))
        if not card_type and getattr(card, "card_type_id", None):
            card_type = session.get(CardType, card.card_type_id)
        if not card_type:
            continue
        if getattr(card, "ai_context_template", None) is None:
            card.ai_context_template = getattr(card_type, "default_ai_context_template", None)
        if getattr(card, "ai_context_template_review", None) is None:
            card.ai_context_template_review = getattr(card_type, "default_ai_context_template_review", None)

    # Auto-sync unmapped built-in response models into CardType.
    # Purpose: keep settings/card-type model definitions visible after adding models.
    # mapped_model_keys = set(TYPE_TO_MODEL_KEY.values())
    # for model_key, model_class in RESPONSE_MODEL_MAP.items():
    #     # Skip models explicitly managed by default_types.
    #     if model_key in mapped_model_keys:
    #         continue

    #     existing = next(
    #         (
    #             ct for ct in existing_types
    #             if ct.name == model_key or ct.model_name == model_key
    #         ),
    #         None
    #     )

    #     schema = None
    #     try:
    #         schema = model_class.model_json_schema(ref_template="#/$defs/{model}")
    #     except Exception:
    #         schema = None

    #     if existing:
    #         # Only repair built-in types; do not overwrite user custom types.
    #         if getattr(existing, "built_in", False):
    #             existing.model_name = model_key
    #             if schema is not None:
    #                 existing.json_schema = schema
    #             if not (existing.description or "").strip():
    #                 existing.description = f"{model_key} (built-in response model)"
    #         continue

    #     auto_type = CardType(
    #         name=model_key,
    #         model_name=model_key,
    #         description=f"{model_key} (built-in response model)",
    #         json_schema=schema,
    #         ai_params=None,
    #         editor_component=None,
    #         is_ai_enabled=False,
    #         is_singleton=False,
    #         default_ai_context_template=None,
    #         built_in=True,
    #     )
    #     session.add(auto_type)
    #     existing_types.append(auto_type)
    #     existing_type_names.add(model_key)
    #     existing_type_by_name[model_key] = auto_type
    #     logger.info(f"Created builtin response model card type: {model_key}")

    session.commit()
    logger.info(f"Default card types committed. overwrite_card_schemas={overwrite_card_schemas}")
