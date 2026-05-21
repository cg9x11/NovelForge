from __future__ import annotations
from app.locales import localized_text

import re
import unicodedata
from typing import Dict, Optional

PROMPT_NAME_TO_KEY: Dict[str, str] = {
    "ai_cuong_mot_oan": "paragraph_outline",
    "dai_cuong_mot_doan": "paragraph_outline",
    localized_text('hardcoded.services_builtin_key_registry_26a8fe18'): "idea_chat",
    "Trò chuyện ý tưởng": "idea_chat",
    "Hội thoại khơi nguồn cảm hứng": "idea_chat",
    localized_text('hardcoded.services_builtin_key_registry_ee419b65'): "idea_chat_react",
    "Trò chuyện ý tưởng-React": "idea_chat_react",
    "Trò chuyện ý tưởng - React": "idea_chat_react",
    "Hội thoại khơi nguồn cảm hứng - React": "idea_chat_react",
    localized_text('hardcoded.services_builtin_key_registry_a5fe456c'): "workflow_agent",
    "Workflow Agent": "workflow_agent",
    localized_text('hardcoded.services_builtin_key_registry_0fb4fd73'): "workflow_agent_react",
    "Workflow Agent - React": "workflow_agent_react",
    localized_text('hardcoded.services_builtin_key_registry_284d3903'): "one_sentence",
    "Tóm tắt một câu": "one_sentence",
    localized_text('hardcoded.services_builtin_key_registry_7d7398ad'): "paragraph_outline",
    "Đề cương một đoạn": "paragraph_outline",
    localized_text('hardcoded.services_builtin_key_registry_f0b2ba1c'): "world_building",
    "Thiết lập thế giới quan": "world_building",
    localized_text('hardcoded.services_builtin_key_registry_01f65785'): "blueprint",
    "Bản thiết kế cốt lõi": "blueprint",
    localized_text('hardcoded.services_builtin_key_registry_63497248'): "volume_outline",
    "Đề cương phân quyển": "volume_outline",
    localized_text('hardcoded.services_builtin_key_registry_8a1f5e45'): "stage_outline",
    "Đề cương giai đoạn": "stage_outline",
    localized_text('hardcoded.services_builtin_key_registry_52ab0871'): "chapter_outline",
    "Đề cương chương": "chapter_outline",
    localized_text('hardcoded.services_builtin_key_registry_fdd877a3'): "writing_guide",
    "Hướng dẫn viết": "writing_guide",
    localized_text('hardcoded.services_builtin_key_registry_0f178db9'): "content_generation",
    "Tạo nội dung": "content_generation",
    localized_text('hardcoded.services_builtin_key_registry_e5911d2a'): "expansion",
    "Viết mở rộng": "expansion",
    localized_text('hardcoded.services_builtin_key_registry_334886b0'): "polish",
    "Trau chuốt văn phong": "polish",
    localized_text('hardcoded.services_builtin_key_registry_3cd21226'): "special_ability_generation",
    "Tạo bàn tay vàng": "special_ability_generation",
    localized_text('hardcoded.services_builtin_key_registry_0d5fbc4f'): "relationship_extraction",
    "Trích xuất quan hệ": "relationship_extraction",
    localized_text('hardcoded.services_builtin_key_registry_59510c94'): "character_dynamic_info_extraction",
    "Trích xuất thông tin động của nhân vật": "character_dynamic_info_extraction",
    localized_text('hardcoded.services_builtin_key_registry_b12a6b0d'): "scene_state_extraction",
    "Trích xuất trạng thái bối cảnh": "scene_state_extraction",
    localized_text('hardcoded.services_builtin_key_registry_5aa2db94'): "organization_state_extraction",
    "Trích xuất trạng thái tổ chức": "organization_state_extraction",
    localized_text('hardcoded.services_builtin_key_registry_325ee9cc'): "item_state_extraction",
    "Trích xuất trạng thái vật phẩm": "item_state_extraction",
    localized_text('hardcoded.services_builtin_key_registry_fc5106b0'): "concept_state_extraction",
    "Trích xuất mức độ nắm bắt khái niệm": "concept_state_extraction",
    localized_text('hardcoded.services_builtin_key_registry_a1d0db03'): "general_review",
    "Kiểm duyệt chung": "general_review",
    localized_text('hardcoded.services_builtin_key_registry_4e5760f2'): "chapter_review",
    "Duyệt chương": "chapter_review",
    localized_text('hardcoded.services_builtin_key_registry_a512d1c4'): "stage_review",
    "Duyệt giai đoạn": "stage_review",
    localized_text('hardcoded.services_builtin_key_registry_584a71c3'): "instruction_flow_guide",
    "Quy phạm tạo luồng lệnh": "instruction_flow_guide",
}

CARD_TYPE_NAME_TO_KEY: Dict[str, str] = {
    localized_text('hardcoded.services_builtin_key_registry_75658131'): "general_text",
    "Văn bản chung": "general_text",
    localized_text('hardcoded.services_builtin_key_registry_e35ebe16'): "work_tags",
    "Tags tác phẩm": "work_tags",
    localized_text('hardcoded.services_builtin_key_registry_42858fc9'): "special_ability",
    "Bàn tay vàng": "special_ability",
    localized_text('hardcoded.services_builtin_key_registry_284d3903'): "one_sentence",
    "Tóm tắt một câu": "one_sentence",
    localized_text('hardcoded.services_builtin_key_registry_95d4bda1'): "story_outline",
    "Đại cương cốt truyện": "story_outline",
    localized_text('hardcoded.services_builtin_key_registry_f0b2ba1c'): "world_building",
    "Thiết lập thế giới quan": "world_building",
    localized_text('hardcoded.services_builtin_key_registry_01f65785'): "blueprint",
    "Bản thiết kế cốt lõi": "blueprint",
    localized_text('hardcoded.services_builtin_key_registry_63497248'): "volume_outline",
    "Đề cương phân quyển": "volume_outline",
    localized_text('hardcoded.services_builtin_key_registry_fdd877a3'): "writing_guide",
    "Hướng dẫn viết": "writing_guide",
    localized_text('hardcoded.services_builtin_key_registry_8a1f5e45'): "stage_outline",
    "Đề cương giai đoạn": "stage_outline",
    localized_text('hardcoded.services_builtin_key_registry_52ab0871'): "chapter_outline",
    "Đề cương chương": "chapter_outline",
    localized_text('hardcoded.services_builtin_key_registry_177cf82a'): "chapter_body",
    "Chính văn chương": "chapter_body",
    localized_text('hardcoded.services_builtin_key_registry_1a9fa122'): "review_result_card",
    localized_text('hardcoded.services_builtin_key_registry_b0a8d18d'): "review_result_card",
    "Thẻ duyệt nội dung": "review_result_card",
    localized_text('hardcoded.services_builtin_key_registry_5faece5e'): "character_card",
    "Thẻ nhân vật": "character_card",
    localized_text('hardcoded.services_builtin_key_registry_f02fb443'): "scene_card",
    "Thẻ bối cảnh": "scene_card",
    localized_text('hardcoded.services_builtin_key_registry_95343eb3'): "organization_card",
    "Thẻ tổ chức": "organization_card",
    localized_text('hardcoded.services_builtin_key_registry_21efdd97'): "item_card",
    "Thẻ vật phẩm": "item_card",
    localized_text('hardcoded.services_builtin_key_registry_c86a526f'): "concept_card",
    "Thẻ khái niệm": "concept_card",
    localized_text('hardcoded.services_builtin_key_registry_46ecac29'): "folder",
    "Thư mục": "folder",
}

KNOWLEDGE_NAME_TO_KEY: Dict[str, str] = {
    localized_text('hardcoded.services_builtin_key_registry_f4995d59'): "naming_guide",
    "Hướng dẫn đặt tên": "naming_guide",
    localized_text('hardcoded.services_builtin_key_registry_e35ebe16'): "work_tags",
    "Tags tác phẩm": "work_tags",
    localized_text('hardcoded.services_builtin_key_registry_fd1a589c'): "style_constraints",
    "Ràng buộc văn phong": "style_constraints",
    localized_text('hardcoded.services_builtin_key_registry_1d02b0c0'): "item_categories",
    "Phân loại vật phẩm": "item_categories",
    localized_text('hardcoded.services_builtin_key_registry_6494d2fb'): "concept_categories",
    "Phân loại khái niệm": "concept_categories",
}

KEY_TO_PROMPT_NAME = {v: k for k, v in reversed(list(PROMPT_NAME_TO_KEY.items()))}

def slugify_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or "").replace(chr(273), "d").replace(chr(272), "D")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower().replace("đ", "d")
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return ascii_text or (name or "").strip()


def legacy_slugify_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or "").replace(chr(273), "d").replace(chr(272), "D")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower().replace("\u0111", "d").replace("\u0110", "d").replace("??", "d")
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return ascii_text or (name or "").strip()
def resolve_builtin_key(name: Optional[str], mapping: Dict[str, str]) -> Optional[str]:
    value = (name or "").strip()
    if not value:
        return None
    return mapping.get(value) or slugify_name(value)
