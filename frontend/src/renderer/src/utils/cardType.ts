const CARD_TYPE_NAME_TO_KEY: Record<string, string> = {
  '章节正文': 'chapter_body',
  '内容审核卡片': 'review_result_card',
  '分卷大纲': 'volume_outline',
  '阶段大纲': 'stage_outline',
  '章节大纲': 'chapter_outline',
  '角色卡': 'character_card',
  '场景卡': 'scene_card'
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
