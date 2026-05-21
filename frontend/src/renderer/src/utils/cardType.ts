import { i18n } from '@renderer/i18n'

const legacyText = (...codes: number[]) => String.fromCharCode(...codes)

const CARD_TYPE_NAME_TO_KEY: Record<string, string> = {
  [legacyText(36890, 29992, 25991, 26412)]: 'general_text',
  [legacyText(20316, 21697, 26631, 31614)]: 'work_tags',
  [legacyText(37329, 25163, 25351)]: 'special_ability',
  [legacyText(19968, 21477, 35805, 26775, 27010)]: 'one_sentence',
  [legacyText(25925, 20107, 22823, 32434)]: 'story_outline',
  [legacyText(19990, 30028, 35266, 35774, 23450)]: 'world_building',
  [legacyText(26680, 24515, 34013, 22270)]: 'blueprint',
  [legacyText(20998, 21367, 22823, 32434)]: 'volume_outline',
  [legacyText(20889, 20316, 25351, 21335)]: 'writing_guide',
  [legacyText(38454, 27573, 22823, 32434)]: 'stage_outline',
  [legacyText(31456, 33410, 22823, 32434)]: 'chapter_outline',
  [legacyText(31456, 33410, 27491, 25991)]: 'chapter_body',
  [legacyText(20869, 23481, 23457, 26680, 21345, 29255)]: 'review_result_card',
  [legacyText(20869, 23481, 23457, 26680)]: 'review_result_card',
  [legacyText(35282, 33394, 21345)]: 'character_card',
  [legacyText(22330, 26223, 21345)]: 'scene_card',
  [legacyText(32452, 32455, 21345)]: 'organization_card',
  [legacyText(29289, 21697, 21345)]: 'item_card',
  [legacyText(27010, 24565, 21345)]: 'concept_card',
}


function getLocaleAliasKey(name: string): string | null {
  const messages = i18n.global.messages.value as Record<string, any>
  for (const localeMessages of Object.values(messages)) {
    const aliases = localeMessages?.card_type_legacy_aliases || {}
    for (const [key, values] of Object.entries(aliases)) {
      if (Array.isArray(values) && values.includes(name)) return key
    }
  }
  return null
}

const CARD_TYPE_KEYS = new Set([
  'general_text',
  'work_tags',
  'special_ability',
  'one_sentence',
  'story_outline',
  'world_building',
  'blueprint',
  'volume_outline',
  'writing_guide',
  'stage_outline',
  'chapter_outline',
  'chapter_body',
  'review_result_card',
  'character_card',
  'scene_card',
  'organization_card',
  'item_card',
  'concept_card'
])

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
  return cardType.key || CARD_TYPE_MODEL_TO_KEY[cardType.output_model_name] || (CARD_TYPE_KEYS.has(cardType.name) ? cardType.name : null) || CARD_TYPE_NAME_TO_KEY[cardType.name] || getLocaleAliasKey(cardType.name) || null
}

export function isCardType(cardType: any, expectedKey: string): boolean {
  return getCardTypeKey(cardType) === expectedKey
}
