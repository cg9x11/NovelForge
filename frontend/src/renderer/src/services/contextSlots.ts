import type { CardRead, CardUpdate } from '@renderer/api/cards'
import { i18n } from '@renderer/i18n'

export type ContextTemplateKind = 'generation' | 'review'

export interface ContextTemplates {
  generation: string
  review: string
}

export const CONTEXT_TEMPLATE_LABELS: Record<ContextTemplateKind, string> = {
  get generation() { return String(i18n.global.t('context_templates.labels.generation')) },
  get review() { return String(i18n.global.t('context_templates.labels.review')) },
}

export function normalizeContextTemplateKind(
  kind: ContextTemplateKind | string | null | undefined,
  fallback: ContextTemplateKind = 'generation'
): ContextTemplateKind {
  return kind === 'review' || kind === 'generation' ? kind : fallback
}

export function getCardContextTemplates(card: Partial<CardRead> | null | undefined): ContextTemplates {
  return {
    generation: String((card as any)?.ai_context_template || ''),
    review: String((card as any)?.ai_context_template_review || ''),
  }
}

export function cloneContextTemplates(templates?: Partial<ContextTemplates> | null): ContextTemplates {
  return {
    generation: String(templates?.generation || ''),
    review: String(templates?.review || ''),
  }
}

export function getContextTemplateByKind(
  card: Partial<CardRead> | null | undefined,
  templates: Partial<ContextTemplates> | null | undefined,
  kind: ContextTemplateKind | string | null | undefined,
  fallback: ContextTemplateKind = 'generation'
): string {
  const normalizedKind = normalizeContextTemplateKind(kind, fallback)
  const resolvedTemplates = templates ? cloneContextTemplates(templates) : getCardContextTemplates(card)
  return resolvedTemplates[normalizedKind]
}

export function buildContextTemplateUpdatePayload(templates: ContextTemplates): Pick<CardUpdate, 'ai_context_template'> & {
  ai_context_template: string
  ai_context_template_review: string
} {
  return {
    ai_context_template: templates.generation,
    ai_context_template_review: templates.review,
  }
}
