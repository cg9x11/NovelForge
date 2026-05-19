const CARD_TYPE_NAME_TO_KEY: Record<string, string> = {
  '通用文本': 'general_text',
  'Văn bản chung': 'general_text',
  '作品标签': 'work_tags',
  'Tags tác phẩm': 'work_tags',
  '金手指': 'special_ability',
  'Bàn tay vàng': 'special_ability',
  '一句话梗概': 'one_sentence',
  'Tóm tắt một câu': 'one_sentence',
  '故事大纲': 'story_outline',
  'Đại cương cốt truyện': 'story_outline',
  '世界观设定': 'world_building',
  'Thiết lập thế giới quan': 'world_building',
  '核心蓝图': 'blueprint',
  'Bản thiết kế cốt lõi': 'blueprint',
  '分卷大纲': 'volume_outline',
  'Đề cương phân quyển': 'volume_outline',
  '写作指南': 'writing_guide',
  'Hướng dẫn viết': 'writing_guide',
  '阶段大纲': 'stage_outline',
  'Đề cương giai đoạn': 'stage_outline',
  '章节大纲': 'chapter_outline',
  'Đề cương chương': 'chapter_outline',
  '章节正文': 'chapter_body',
  'Chính văn chương': 'chapter_body',
  '内容审核卡片': 'review_result_card',
  '内容审核': 'review_result_card',
  'Thẻ duyệt nội dung': 'review_result_card',
  '角色卡': 'character_card',
  'Thẻ nhân vật': 'character_card',
  '场景卡': 'scene_card',
  'Thẻ bối cảnh': 'scene_card',
  '组织卡': 'organization_card',
  'Thẻ tổ chức': 'organization_card',
  '物品卡': 'item_card',
  'Thẻ vật phẩm': 'item_card',
  '概念卡': 'concept_card',
  'Thẻ khái niệm': 'concept_card'
}

const CARD_TYPE_MODEL_TO_KEY: Record<string, string> = {
  Chapter: 'chapter_body',
  ReviewResultCardContent: 'review_result_card',
  VolumeOutline: 'volume_outline',
  StageLine: 'stage_outline',
  ChapterOutline: 'chapter_outline',
  CharacterCard: 'character_card',
  SceneCard: 'scene_card',
  OrganizationCard: 'organization_card',
  ItemCard: 'item_card',
  ConceptCard: 'concept_card'
}

export function getCardTypeKey(cardType: any): string | null {
  if (!cardType) return null
  return cardType.key || CARD_TYPE_MODEL_TO_KEY[cardType.output_model_name] || CARD_TYPE_NAME_TO_KEY[cardType.name] || null
}

export function isCardType(cardType: any, expectedKey: string): boolean {
  return getCardTypeKey(cardType) === expectedKey
}
