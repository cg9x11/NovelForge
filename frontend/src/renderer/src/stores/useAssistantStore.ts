import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { i18n } from '@renderer/i18n'
import { getProjects, type ProjectRead } from '@renderer/api/projects'
import { getCardsForProject, type CardRead } from '@renderer/api/cards'
import type {
  AssistantRef,
  AssistantCardRef,
  AssistantRefSource,
  ChapterExcerptRef,
  ReviewResultRef,
} from '@renderer/api/ai'

export type InjectRef = AssistantRef
export type AssistantMessage = { role: 'user' | 'assistant'; content: string; ts?: number }

function getInjectedRefKey(ref: InjectRef): string {
  if (ref.refType === 'card') return `card:${ref.projectId}:${ref.cardId}`
  if (ref.refType === 'chapter_excerpt') {
    return `chapter_excerpt:${ref.projectId}:${ref.cardId}:${ref.fieldPath}:${ref.startLine}:${ref.endLine}:${ref.snapshotHash}`
  }
  return `review_result:${ref.projectId}:${ref.reviewCardId}`
}

function normalizeInjectedRef(ref: Partial<InjectRef> & Record<string, any>, source: AssistantRefSource): InjectRef | null {
  if (!ref) return null
  const refType = (ref.refType || 'card') as InjectRef['refType']

  if (refType === 'card') {
    if (!ref.projectId || !ref.cardId) return null
    return {
      refType: 'card',
      projectId: Number(ref.projectId),
      projectName: String(ref.projectName || ''),
      cardId: Number(ref.cardId),
      cardTitle: String(ref.cardTitle || ''),
      content: ref.content ?? {},
      source,
    }
  }

  if (refType === 'chapter_excerpt') {
    if (!ref.projectId || !ref.cardId || !ref.startLine || !ref.endLine || !ref.snapshotHash) return null
    return {
      refType: 'chapter_excerpt',
      projectId: Number(ref.projectId),
      projectName: String(ref.projectName || ''),
      cardId: Number(ref.cardId),
      cardTitle: String(ref.cardTitle || ''),
      fieldPath: String(ref.fieldPath || 'content'),
      startLine: Number(ref.startLine),
      endLine: Number(ref.endLine),
      text: String(ref.text || ''),
      numberedText: String(ref.numberedText || ''),
      snapshotHash: String(ref.snapshotHash),
      source,
    }
  }

  if (!ref.projectId || !ref.reviewCardId || !ref.targetId) return null
  return {
    refType: 'review_result',
    projectId: Number(ref.projectId),
    reviewCardId: Number(ref.reviewCardId),
    targetId: Number(ref.targetId),
    targetTitle: String(ref.targetTitle || ''),
    reviewType: String(ref.reviewType || 'card'),
    reviewProfile: ref.reviewProfile ?? null,
    qualityGate: String(ref.qualityGate || 'revise'),
    resultText: String(ref.resultText || ''),
    contentSnapshot: ref.contentSnapshot ?? null,
    source,
  }
}

export interface CardContextInfo {
  card_id: number
  title: string
  card_type: string
  parent_id: number | null
  project_id: number
  first_seen: number  // timestamp
  last_seen: number   // timestamp
  access_count: number
}

export interface UserOperation {
  timestamp: number
  type: 'create' | 'edit' | 'delete' | 'move'
  cardId: number
  cardTitle: string
  cardType: string
  detail?: string
}

export interface ProjectStructureContext {
  project_id: number
  project_name: string
  total_cards: number
  stats: Record<string, number>
  tree_text: string
  available_card_types: string[]
  last_updated: number
  version: number
}

const ENV_PREFIX = (import.meta as any)?.env?.MODE || 'production'
const HISTORY_KEY_PREFIX = `nf:${ENV_PREFIX}:assistant:history:`
const STRUCTURE_KEY_PREFIX = `nf:${ENV_PREFIX}:assistant:structure:`
const OPERATIONS_KEY_PREFIX = `nf:${ENV_PREFIX}:assistant:operations:`

function projectHistoryKey(projectId: number) { return `${HISTORY_KEY_PREFIX}${projectId}` }
function projectStructureKey(projectId: number) { return `${STRUCTURE_KEY_PREFIX}${projectId}` }
function projectOperationsKey(projectId: number) { return `${OPERATIONS_KEY_PREFIX}${projectId}` }

export const useAssistantStore = defineStore('assistant', () => {
  const projects = ref<ProjectRead[]>([])
  const cardsByProject = shallowRef<Record<number, CardRead[]>>({})
  const injectedRefs = shallowRef<InjectRef[]>([])

  const activeCardContext = ref<CardContextInfo | null>(null)
  const cardRegistry = ref<Map<number, CardContextInfo>>(new Map())
  const projectCardTypes = ref<string[]>([])

  const projectStructure = ref<ProjectStructureContext | null>(null)

  const recentOperations = ref<UserOperation[]>([])

  async function loadProjects() {
    projects.value = await getProjects()
  }

  async function loadCardsForProject(pid: number) {
    const list = await getCardsForProject(pid)
    cardsByProject.value = { ...cardsByProject.value, [pid]: list }
    return list
  }

  function addInjectedRefs(pid: number, pname: string, ids: number[]) {
    const list = cardsByProject.value[pid] || []
    const map = new Map<number, CardRead>()
    list.forEach(c => map.set(c.id, c))

    const newRefs = [...injectedRefs.value]

    for (const id of ids) {
      const c = map.get(id)
      if (!c) continue
      const nextRef: AssistantCardRef = {
        refType: 'card',
        projectId: pid,
        projectName: pname,
        cardId: id,
        cardTitle: c.title,
        content: (c as any).content,
        source: 'manual',
      }
      const key = getInjectedRefKey(nextRef)
      const existingIdx = newRefs.findIndex(r => getInjectedRefKey(r) === key)
      if (existingIdx >= 0) {
        const prev = newRefs[existingIdx]
        newRefs[existingIdx] = { ...prev, ...nextRef, source: 'manual' } as InjectRef
        continue
      }
      newRefs.push(nextRef)
    }

    injectedRefs.value = newRefs
  }

  function addInjectedRefDirect(ref: InjectRef | (Partial<InjectRef> & Record<string, any>), source: AssistantRefSource = 'manual') {
    const normalizedRef = normalizeInjectedRef(ref as any, source)
    if (!normalizedRef) return

    const newRefs = [...injectedRefs.value]
    const key = getInjectedRefKey(normalizedRef)
    const idx = newRefs.findIndex(r => getInjectedRefKey(r) === key)
    const prev = idx >= 0 ? newRefs[idx] : null

    if (idx >= 0) {
      if (prev?.source === 'manual' && source === 'auto') {
        newRefs[idx] = { ...prev, ...normalizedRef, source: 'manual' } as InjectRef
      } else {
        newRefs[idx] = { ...prev, ...normalizedRef, source } as InjectRef
      }
    } else {
      newRefs.push(normalizedRef)
    }

    injectedRefs.value = newRefs
  }

  function clearAutoRefs() {
    injectedRefs.value = injectedRefs.value.filter(r => r.source !== 'auto')
  }

  function addAutoRef(ref: InjectRef) {
    clearAutoRefs()
    addInjectedRefDirect(ref, 'auto')
  }

  function addChapterExcerptRef(ref: ChapterExcerptRef, source: AssistantRefSource = 'manual') {
    addInjectedRefDirect(ref, source)
  }

  function addReviewResultRef(ref: ReviewResultRef, source: AssistantRefSource = 'manual') {
    addInjectedRefDirect(ref, source)
  }

  function removeInjectedRefAt(index: number) {
    injectedRefs.value = injectedRefs.value.filter((_, i) => i !== index)
  }
  function clearInjectedRefs() { injectedRefs.value = [] }

  function getHistory(projectId: number): AssistantMessage[] {
    try {
      const raw = localStorage.getItem(projectHistoryKey(projectId))
      if (!raw) return []
      const arr = JSON.parse(raw)
      if (!Array.isArray(arr)) return []
      return arr as AssistantMessage[]
    } catch { return [] }
  }

  function setHistory(projectId: number, history: AssistantMessage[]) {
    try {
      localStorage.setItem(projectHistoryKey(projectId), JSON.stringify(history || []))
    } catch {}
  }

  function appendHistory(projectId: number, msg: AssistantMessage) {
    const hist = getHistory(projectId)
    hist.push({ ...msg, ts: msg.ts ?? Date.now() })
    setHistory(projectId, hist)
  }

  function clearHistory(projectId: number) {
    try { localStorage.removeItem(projectHistoryKey(projectId)) } catch {}
  }

  function updateActiveCard(card: CardRead | null, projectId: number) {
    if (!card) {
      activeCardContext.value = null
      console.log('[AssistantStore] clear active card')
      return
    }

    const now = Date.now()
    const info: CardContextInfo = {
      card_id: card.id,
      title: card.title,
      card_type: (card as any).card_type?.name || 'Unknown',
      parent_id: (card as any).parent_id || null,
      project_id: projectId,
      first_seen: now,
      last_seen: now,
      access_count: 1
    }


    activeCardContext.value = info

    registerCard(info)
  }

  function registerCard(info: CardContextInfo) {
    const existing = cardRegistry.value.get(info.card_id)
    if (existing) {
      cardRegistry.value.set(info.card_id, {
        ...existing,
        title: info.title,
        card_type: info.card_type,
        last_seen: Date.now(),
        access_count: existing.access_count + 1
      })
    } else {
      cardRegistry.value.set(info.card_id, info)
    }
  }

  function updateProjectCardTypes(types: string[]) {
    projectCardTypes.value = types
  }

  function getContextForAssistant(): {
    active_card: CardContextInfo | null
    recent_cards: CardContextInfo[]
    card_types: string[]
  } {
    const recent = Array.from(cardRegistry.value.values())
      .sort((a, b) => b.last_seen - a.last_seen)
      .slice(0, 10)

    return {
      active_card: activeCardContext.value,
      recent_cards: recent,
      card_types: projectCardTypes.value
    }
  }

  function clearCardContext() {
    activeCardContext.value = null
    cardRegistry.value.clear()
    projectCardTypes.value = []
  }


  function loadProjectStructureFromCache(projectId: number): ProjectStructureContext | null {
    try {
      const raw = localStorage.getItem(projectStructureKey(projectId))
      if (!raw) return null
      const data = JSON.parse(raw)
      return data as ProjectStructureContext
    } catch {
      return null
    }
  }

  function saveProjectStructureToCache(structure: ProjectStructureContext) {
    try {
      localStorage.setItem(projectStructureKey(structure.project_id), JSON.stringify(structure))
    } catch (e) {
    }
  }

  function buildCardTreeText(cards: CardRead[], parentId: number | null = null, depth: number = 0, currentCardId?: number): string {
    const indent = depth === 0 ? '' : '│  '.repeat(depth - 1) + '├─ '
    const children = cards.filter(c => (c as any).parent_id === parentId)
      .sort((a, b) => ((a as any).display_order || 0) - ((b as any).display_order || 0))

    const lines: string[] = []

    for (let i = 0; i < children.length; i++) {
      const card = children[i]
      const typeName = (card as any).card_type?.name || 'Unknown'
      const updatedAt = (card as any).updated_at
      const updatedDate = updatedAt ? new Date(updatedAt).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) : ''
      const isCurrent = currentCardId && card.id === currentCardId
      const marker = isCurrent ? ` ${i18n.global.t('assistant_store.current_marker')}` : ''

      lines.push(`${indent}[${typeName}] ${card.title} {id:${card.id} | ${i18n.global.t('assistant_store.updated_label')}:${updatedDate}${marker}}`)

      const childText = buildCardTreeText(cards, card.id, depth + 1, currentCardId)
      if (childText) {
        lines.push(childText)
      }
    }

    return lines.join('\n')
  }

  function buildProjectStructure(
    projectId: number,
    projectName: string,
    cards: CardRead[],
    cardTypes: any[],
    currentCardId?: number
  ): ProjectStructureContext {
    const stats: Record<string, number> = {}
    for (const card of cards) {
      const typeName = (card as any).card_type?.name || i18n.global.t('assistant_store.uncategorized')
      stats[typeName] = (stats[typeName] || 0) + 1
    }

    const treeText = buildCardTreeText(cards, null, 0, currentCardId)

    const availableTypes = cardTypes.map(ct => ct.name)

    return {
      project_id: projectId,
      project_name: projectName,
      total_cards: cards.length,
      stats,
      tree_text: treeText || `ROOT\n(${i18n.global.t('assistant_store.no_cards')})`,
      available_card_types: availableTypes,
      last_updated: Date.now(),
      version: cards.length
    }
  }

  function updateProjectStructure(
    projectId: number,
    projectName: string,
    cards: CardRead[],
    cardTypes: any[],
    currentCardId?: number,
    forceRebuild: boolean = false
  ) {
    if (!forceRebuild) {
      const cached = loadProjectStructureFromCache(projectId)
      if (cached && cached.version === cards.length) {
        const updated = buildProjectStructure(projectId, projectName, cards, cardTypes, currentCardId)
        projectStructure.value = updated
        saveProjectStructureToCache(updated)
        return
      }
    }

    const structure = buildProjectStructure(projectId, projectName, cards, cardTypes, currentCardId)
    projectStructure.value = structure
    saveProjectStructureToCache(structure)
  }

  function clearProjectStructure() {
    projectStructure.value = null
  }


  function loadOperationsFromCache(projectId: number): UserOperation[] {
    try {
      const raw = localStorage.getItem(projectOperationsKey(projectId))
      if (!raw) return []
      const arr = JSON.parse(raw)
      if (!Array.isArray(arr)) return []
      return arr as UserOperation[]
    } catch {
      return []
    }
  }

  function saveOperationsToCache(projectId: number, operations: UserOperation[]) {
    try {
      localStorage.setItem(projectOperationsKey(projectId), JSON.stringify(operations))
    } catch (e) {
    }
  }

  function recordOperation(projectId: number, op: Omit<UserOperation, 'timestamp'>) {
    const operation: UserOperation = {
      ...op,
      timestamp: Date.now()
    }

    recentOperations.value.unshift(operation)

    if (recentOperations.value.length > 3) {
      recentOperations.value = recentOperations.value.slice(0, 3)
    }

    saveOperationsToCache(projectId, recentOperations.value)

  }

  function loadOperations(projectId: number) {
    recentOperations.value = loadOperationsFromCache(projectId)
  }

  function formatRecentOperations(): string {
    if (recentOperations.value.length === 0) return ''

    const lines = recentOperations.value.map((op, idx) => {
      const time = new Date(op.timestamp).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
      const emoji = op.type === 'create' ? '➕' :
                    op.type === 'edit' ? '✏️' :
                    op.type === 'move' ? '📦' :
                    '🗑️'
      const action = op.type === 'create' ? i18n.global.t('assistant_store.actions.create') :
                     op.type === 'edit' ? i18n.global.t('assistant_store.actions.edit') :
                     op.type === 'move' ? i18n.global.t('assistant_store.actions.move') :
                     i18n.global.t('assistant_store.actions.delete')

      let line = `${idx + 1}. [${time}] ${emoji} ${action} "${op.cardTitle}" (${op.cardType} #${op.cardId})`

      if (op.detail) {
        line += `\n   ${i18n.global.t('assistant_store.detail_label')}: ${op.detail}`
      }

      return line
    })

    return lines.join('\n')
  }

  function clearOperations(projectId: number) {
    recentOperations.value = []
    try {
      localStorage.removeItem(projectOperationsKey(projectId))
    } catch {}
  }

  return {
    projects, cardsByProject, injectedRefs,
    loadProjects, loadCardsForProject,
    addInjectedRefs, addInjectedRefDirect, addAutoRef, addChapterExcerptRef, addReviewResultRef, clearAutoRefs, removeInjectedRefAt, clearInjectedRefs,
    getHistory, setHistory, appendHistory, clearHistory,
    updateActiveCard, registerCard, updateProjectCardTypes, getContextForAssistant, clearCardContext,
    activeCardContext, cardRegistry, projectCardTypes,
    projectStructure,
    updateProjectStructure,
    clearProjectStructure,
    recentOperations,
    recordOperation,
    loadOperations,
    formatRecentOperations,
    clearOperations
  }
})
