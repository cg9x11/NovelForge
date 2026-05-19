from __future__ import annotations

import re
import unicodedata
from typing import Dict, Optional

PROMPT_NAME_TO_KEY: Dict[str, str] = {
    "灵感对话": "idea_chat",
    "Trò chuyện ý tưởng": "idea_chat",
    "Hội thoại khơi nguồn cảm hứng": "idea_chat",
    "灵感对话-React": "idea_chat_react",
    "Trò chuyện ý tưởng-React": "idea_chat_react",
    "Trò chuyện ý tưởng - React": "idea_chat_react",
    "Hội thoại khơi nguồn cảm hứng - React": "idea_chat_react",
    "工作流智能体": "workflow_agent",
    "Workflow Agent": "workflow_agent",
    "工作流智能体-React": "workflow_agent_react",
    "Workflow Agent - React": "workflow_agent_react",
    "一句话梗概": "one_sentence",
    "Tóm tắt một câu": "one_sentence",
    "一段话大纲": "paragraph_outline",
    "Đề cương một đoạn": "paragraph_outline",
    "世界观设定": "world_building",
    "Thiết lập thế giới quan": "world_building",
    "核心蓝图": "blueprint",
    "Bản thiết kế cốt lõi": "blueprint",
    "分卷大纲": "volume_outline",
    "Đề cương phân quyển": "volume_outline",
    "阶段大纲": "stage_outline",
    "Đề cương giai đoạn": "stage_outline",
    "章节大纲": "chapter_outline",
    "Đề cương chương": "chapter_outline",
    "写作指南": "writing_guide",
    "Hướng dẫn viết": "writing_guide",
    "内容生成": "content_generation",
    "Tạo nội dung": "content_generation",
    "扩写": "expansion",
    "Viết mở rộng": "expansion",
    "润色": "polish",
    "Trau chuốt văn phong": "polish",
    "金手指生成": "special_ability_generation",
    "Tạo bàn tay vàng": "special_ability_generation",
    "关系提取": "relationship_extraction",
    "Trích xuất quan hệ": "relationship_extraction",
    "角色动态信息提取": "character_dynamic_info_extraction",
    "Trích xuất thông tin động của nhân vật": "character_dynamic_info_extraction",
    "场景状态提取": "scene_state_extraction",
    "Trích xuất trạng thái bối cảnh": "scene_state_extraction",
    "组织状态提取": "organization_state_extraction",
    "Trích xuất trạng thái tổ chức": "organization_state_extraction",
    "物品状态提取": "item_state_extraction",
    "Trích xuất trạng thái vật phẩm": "item_state_extraction",
    "概念掌握提取": "concept_state_extraction",
    "Trích xuất mức độ nắm bắt khái niệm": "concept_state_extraction",
    "通用审核": "general_review",
    "Kiểm duyệt chung": "general_review",
    "章节审核": "chapter_review",
    "Duyệt chương": "chapter_review",
    "阶段审核": "stage_review",
    "Duyệt giai đoạn": "stage_review",
    "指令流生成规范": "instruction_flow_guide",
    "Quy phạm tạo luồng lệnh": "instruction_flow_guide",
}

CARD_TYPE_NAME_TO_KEY: Dict[str, str] = {
    "通用文本": "general_text",
    "Văn bản chung": "general_text",
    "作品标签": "work_tags",
    "Tags tác phẩm": "work_tags",
    "金手指": "special_ability",
    "Bàn tay vàng": "special_ability",
    "一句话梗概": "one_sentence",
    "Tóm tắt một câu": "one_sentence",
    "故事大纲": "story_outline",
    "Đại cương cốt truyện": "story_outline",
    "世界观设定": "world_building",
    "Thiết lập thế giới quan": "world_building",
    "核心蓝图": "blueprint",
    "Bản thiết kế cốt lõi": "blueprint",
    "分卷大纲": "volume_outline",
    "Đề cương phân quyển": "volume_outline",
    "写作指南": "writing_guide",
    "Hướng dẫn viết": "writing_guide",
    "阶段大纲": "stage_outline",
    "Đề cương giai đoạn": "stage_outline",
    "章节大纲": "chapter_outline",
    "Đề cương chương": "chapter_outline",
    "章节正文": "chapter_body",
    "Chính văn chương": "chapter_body",
    "内容审核卡片": "review_result_card",
    "内容审核": "review_result_card",
    "Thẻ duyệt nội dung": "review_result_card",
    "角色卡": "character_card",
    "Thẻ nhân vật": "character_card",
    "场景卡": "scene_card",
    "Thẻ bối cảnh": "scene_card",
    "组织卡": "organization_card",
    "Thẻ tổ chức": "organization_card",
    "物品卡": "item_card",
    "Thẻ vật phẩm": "item_card",
    "概念卡": "concept_card",
    "Thẻ khái niệm": "concept_card",
    "文件夹": "folder",
    "Thư mục": "folder",
}

KNOWLEDGE_NAME_TO_KEY: Dict[str, str] = {
    "起名指南": "naming_guide",
    "Hướng dẫn đặt tên": "naming_guide",
    "作品标签": "work_tags",
    "Tags tác phẩm": "work_tags",
    "文风约束": "style_constraints",
    "Ràng buộc văn phong": "style_constraints",
    "物品类别": "item_categories",
    "Phân loại vật phẩm": "item_categories",
    "概念类别": "concept_categories",
    "Phân loại khái niệm": "concept_categories",
}

KEY_TO_PROMPT_NAME = {v: k for k, v in reversed(list(PROMPT_NAME_TO_KEY.items()))}

def slugify_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or "")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower().replace("đ", "d")
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return ascii_text or (name or "").strip()

def resolve_builtin_key(name: Optional[str], mapping: Dict[str, str]) -> Optional[str]:
    value = (name or "").strip()
    if not value:
        return None
    return mapping.get(value) or slugify_name(value)
