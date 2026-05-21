import type { CardRead } from '@renderer/api/cards'
import { getCardTypeKey } from '@renderer/utils/cardType'
import type { AssembleContextResponse } from '@renderer/api/ai'

const legacyText = (...codes: number[]) => String.fromCharCode(...codes)
const LEGACY_SHORT_LIVED = legacyText(30701, 26399)
const SHORT_LIVED = 'short_term'


const CARD_TYPE_NAME_TO_KEY: Record<string, string> = {
  [legacyText(20998, 21367, 22823, 32434)]: 'volume_outline',
  [legacyText(38454, 27573, 22823, 32434)]: 'stage_outline',
  [legacyText(31456, 33410, 22823, 32434)]: 'chapter_outline',
  [legacyText(31456, 33410, 27491, 25991)]: 'chapter_body',
  [legacyText(35282, 33394, 21345)]: 'character_card',
  [legacyText(22330, 26223, 21345)]: 'scene_card',
  [legacyText(32452, 32455, 21345)]: 'organization_card',
  [legacyText(29289, 21697, 21345)]: 'item_card',
  [legacyText(27010, 24565, 21345)]: 'concept_card'
}

function resolveTypeKey(typeName: string): string {
  return CARD_TYPE_NAME_TO_KEY[typeName] || typeName
}

function resolveReferenceKey(typeName: string): string {
  return typeName.startsWith('key:') ? typeName.slice('key:'.length) : resolveTypeKey(typeName)
}


export interface ResolveVars {
  currentCard?: CardRead
  volumeNumber?: number
  chapterNumber?: number
}

export interface ResolveContext {
  template: string
  cards: CardRead[]
  currentCard?: CardRead
  assembledContext?: AssembleContextResponse | null
}

function buildPreorder(cards: CardRead[]): CardRead[] {
  type Node = CardRead & { children: Node[] }
  const map = new Map<number, Node>()
  const nodes: Node[] = cards.map(c => ({ ...(c as CardRead), children: [] }))
  nodes.forEach(n => map.set(n.id, n))
  const roots: Node[] = []
  nodes.forEach(n => {
    if (n.parent_id && map.has(n.parent_id)) map.get(n.parent_id)!.children.push(n)
    else roots.push(n)
  })
  const sortRec = (arr: Node[]) => {
    arr.sort((a, b) => a.display_order - b.display_order)
    arr.forEach(ch => sortRec(ch.children))
  }
  sortRec(roots)
  const out: CardRead[] = []
  const visit = (arr: Node[]) => {
    for (const n of arr) { out.push(n); if ((n as any).children?.length) visit((n as any).children) }
  }
  visit(roots)
  return out
}

function extractVolumeNumberFromTitle(title?: string): number | undefined {
  if (!title) return undefined
  const volumeTitlePattern = new RegExp(`^${legacyText(31532)}(\\d+)${legacyText(21367)}$`)
  const m = title.match(volumeTitlePattern)
  if (m) return parseInt(m[1], 10)
  return undefined
}

function getVolumeNumberFromCard(card?: CardRead): number | undefined {
  if (!card) return undefined
  const c = card.content as any
  const toNum = (v: any) => {
    const n = Number(v)
    return Number.isFinite(n) ? n : undefined
  }
  const byTop = toNum(c?.volume_number)
  if (byTop !== undefined) return byTop
  const byOutline = toNum(c?.volume_outline?.volume_number)
  if (byOutline !== undefined) return byOutline
  const byChapter = toNum(c?.chapter_outline?.volume_number)
  if (byChapter !== undefined) return byChapter
  return extractVolumeNumberFromTitle(card.title)
}

function unwrapVolumeOutline(content: any): any {
  if (!content || typeof content !== 'object') return {}
  if (content.volume_outline && typeof content.volume_outline === 'object') return content.volume_outline
  if (content.VolumeOutline && typeof content.VolumeOutline === 'object') return content.VolumeOutline
  if (content.volumeOutline && typeof content.volumeOutline === 'object') return content.volumeOutline
  if (content.volume_outline_response && typeof content.volume_outline_response === 'object') return content.volume_outline_response
  if (content.VolumeOutlineResponse && typeof content.VolumeOutlineResponse === 'object') return content.VolumeOutlineResponse
  const hallmark = ['stage_lines','main_target','thinking','character_snapshot','branch_line']
  const keys = Object.keys(content)
  if (keys.some(k => hallmark.includes(k))) return content
  return {}
}

function getChapterNumberFromCard(card?: CardRead): number | undefined {
  if (!card) return undefined
  const c = card.content as any
  const toNum = (v: any) => {
    const n = Number(v)
    return Number.isFinite(n) ? n : undefined
  }
  const nTop = toNum(c?.chapter_number)
  if (nTop !== undefined) return nTop
  const n = toNum(c?.chapter_outline?.chapter_number)
  if (n !== undefined) return n
  return undefined
}

function buildVars(ctx: ResolveContext): ResolveVars {
  const v: ResolveVars = {}
  v.currentCard = ctx.currentCard
  v.volumeNumber = getVolumeNumberFromCard(ctx.currentCard)
  v.chapterNumber = getChapterNumberFromCard(ctx.currentCard)
  return v
}

function evalIndexExpr(expr: string, vars: ResolveVars, ctx?: ResolveContext, candidatesLen?: number): number | 'last' | undefined {
  const trimmed = (expr || '').trim()
  if (trimmed === 'last' || trimmed === 'first') return trimmed === 'last' ? 'last' : 1
  if (/^-[0-9]+$/.test(trimmed)) {
    const neg = parseInt(trimmed, 10) // negative
    if (typeof candidatesLen === 'number') return Math.max(1, candidatesLen + 1 + neg)
    return undefined
  }
  // $self.<path>(±int)
  const mSelf = trimmed.match(/^\$self\.(.+?)(?:\s*([+-])\s*(\d+))?$/)
  if (mSelf && ctx?.currentCard) {
    const base = Number(getPathValue(ctx.currentCard, mSelf[1]))
    if (!isNaN(base)) {
      const delta = mSelf[2] && mSelf[3] ? (mSelf[2] === '+' ? parseInt(mSelf[3], 10) : -parseInt(mSelf[3], 10)) : 0
      return base + delta
    }
  }
  // $current.volumeNumber±int
  const vm = vars.volumeNumber
  const m = trimmed.match(/^\$current\.volumeNumber\s*([+-])\s*(\d+)$/)
  if (m && typeof vm === 'number') {
    const op = m[1]
    const n = parseInt(m[2], 10)
    return op === '+' ? vm + n : vm - n
  }
  // $current.chapterNumber
  if (trimmed === '$current.chapterNumber' && typeof vars.chapterNumber === 'number') return vars.chapterNumber
  if (/^\d+$/.test(trimmed)) return parseInt(trimmed, 10)
  if (trimmed === '$current.volumeNumber' && typeof vm === 'number') return vm
  return undefined
}

function selectByType(cards: CardRead[], typeName: string): CardRead[] {
  const typeKey = resolveReferenceKey(typeName)
  return cards.filter(c => getCardTypeKey(c.card_type) === typeKey)
}

function selectByTitle(cards: CardRead[], title: string): CardRead | undefined {
  const exact = cards.find(c => c.title === title)
  if (exact) return exact
  const typeKey = resolveReferenceKey(title)
  if (typeKey !== title || title.startsWith('key:')) return cards.find(c => getCardTypeKey(c.card_type) === typeKey)
  return undefined
}

function selectParent(cards: CardRead[], card?: CardRead): CardRead | undefined {
  if (!card?.parent_id) return undefined
  return cards.find(c => c.id === card.parent_id)
}

function getNearestAncestorOfType(cards: CardRead[], card: CardRead | undefined, typeName: string): CardRead | undefined {
  const typeKey = resolveReferenceKey(typeName)
  let cur = card
  while (cur && cur.parent_id) {
    const parent = cards.find(c => c.id === cur!.parent_id)
    if (!parent) return undefined
    if (getCardTypeKey(parent.card_type) === typeKey) return parent
    cur = parent
  }
  return undefined
}

function filterShortLivedEntityAcrossVolumes(cards: CardRead[], currentCard: CardRead | undefined, list: CardRead[]): CardRead[] {
  const entityTypes = new Set(['character_card', 'scene_card', 'organization_card', 'item_card', 'concept_card'])
  if (!currentCard) return list
  const currentVol = getNearestAncestorOfType(cards, currentCard, 'volume_outline')
  const currentVolId = currentVol?.id
  return list.filter(c => {
    if (!entityTypes.has(getCardTypeKey(c.card_type) || '')) return true
    const lifeSpan = (c.content as any)?.life_span
    if (lifeSpan !== SHORT_LIVED && lifeSpan !== LEGACY_SHORT_LIVED) return true
    const vol = getNearestAncestorOfType(cards, c, 'volume_outline')
    return (vol?.id ?? null) === (currentVolId ?? null)
  })
}

function getPathValue(obj: any, path?: string): any {
  if (!path || path.length === 0) return obj
  return path.split('.').reduce((acc, part) => (acc != null ? acc[part] : undefined), obj)
}

function stringifyValue(val: any): string {
  if (val == null) return ''
  if (typeof val === 'object') return JSON.stringify(val, null, 2)
  return String(val)
}

function getStructuredFacts(ctx: ResolveContext): Record<string, any> {
  return ((ctx.assembledContext as any)?.facts_structured || {}) as Record<string, any>
}

function getFactsTokenValue(token: string, ctx: ResolveContext): any {
  const facts = getStructuredFacts(ctx)
  if (token === 'facts.fact_summaries') return facts.fact_summaries || []
  if (token === 'facts.relation_summaries') return facts.relation_summaries || []
  if (token === 'facts.item_summaries' || token === 'facts.entity:item') return facts.item_summaries || []
  if (token === 'facts.concept_summaries' || token === 'facts.entity:concept') return facts.concept_summaries || []
  return undefined
}

function getKgTokenValue(token: string, ctx: ResolveContext): any {
  const m = token.match(/^kg:(.+)$/)
  if (!m) return undefined
  const entityName = m[1].trim().toLowerCase()
  if (!entityName) return []
  const relations = getStructuredFacts(ctx).relation_summaries
  if (!Array.isArray(relations)) return []
  return relations.filter((item: any) => {
    const a = String(item?.a || '').trim().toLowerCase()
    const b = String(item?.b || '').trim().toLowerCase()
    return a === entityName || b === entityName
  })
}

function evalValueExpr(expr: string, ctx: ResolveContext, vars: ResolveVars): any {
  const trimmed = (expr || '').trim()
  const tryJson = () => {
    try { return JSON.parse(trimmed) } catch { return undefined }
  }
  // $self.<path>(±int)
  const mSelf = trimmed.match(/^\$self\.(.+?)(?:\s*([+-])\s*(\d+))?$/)
  if (mSelf && ctx.currentCard) {
    const baseRaw = getPathValue(ctx.currentCard, mSelf[1])
    const delta = mSelf[2] && mSelf[3] ? (mSelf[2] === '+' ? parseInt(mSelf[3], 10) : -parseInt(mSelf[3], 10)) : 0
    const baseNum = Number(baseRaw)
    if (Number.isFinite(baseNum)) return baseNum + delta
    return baseRaw
  }
  // $parent.<path>(±int)
  const mParent = trimmed.match(/^\$parent\.(.+?)(?:\s*([+-])\s*(\d+))?$/)
  if (mParent) {
    const parent = selectParent(ctx.cards, ctx.currentCard)
    const baseRaw = getPathValue(parent, mParent[1])
    const delta = mParent[2] && mParent[3] ? (mParent[2] === '+' ? parseInt(mParent[3], 10) : -parseInt(mParent[3], 10)) : 0
    const baseNum = Number(baseRaw)
    if (Number.isFinite(baseNum)) return baseNum + delta
    return baseRaw
  }
  const mCurrent = trimmed.match(/^\$current\.(.+?)(?:\s*([+-])\s*(\d+))?$/)
  if (mCurrent && ctx.currentCard) {
    const p = mCurrent[1]
    const full = p.startsWith('content.') ? p : `content.${p}`
    const baseRaw = getPathValue(ctx.currentCard, full)
    const delta = mCurrent[2] && mCurrent[3] ? (mCurrent[2] === '+' ? parseInt(mCurrent[3], 10) : -parseInt(mCurrent[3], 10)) : 0
    const baseNum = Number(baseRaw)
    if (Number.isFinite(baseNum)) return baseNum + delta
    return baseRaw
  }
  if (trimmed.startsWith('$self.')) {
    const p = trimmed.substring('$self.'.length)
    return getPathValue(ctx.currentCard, p)
  }
  if (trimmed.startsWith('$parent.')) {
    const parent = selectParent(ctx.cards, ctx.currentCard)
    const p = trimmed.substring('$parent.'.length)
    return getPathValue(parent, p)
  }
  if (trimmed.startsWith('$current.')) {
    const p = trimmed.substring('$current.'.length)
    const full = p.startsWith('content.') ? p : `content.${p}`
    return getPathValue(ctx.currentCard, full)
  }
  if ((trimmed.startsWith('[') && trimmed.endsWith(']')) || (trimmed.startsWith('{') && trimmed.endsWith('}'))) {
    const j = tryJson(); if (j !== undefined) return j
  }
  if (/^[-+]?\d+(?:\.\d+)?$/.test(trimmed)) return Number(trimmed)
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1)
  }
  return trimmed
}

function toArray(val: any): any[] { if (Array.isArray(val)) return val; if (val == null) return []; return [val] }

type FilterCond = { field: string; op: 'in'|'='|'<'|'>'; rhsRaw: string }
function parseFilterExpr(expr: string): { conditions: FilterCond[] } | null {
  const raw = (expr || '').trim()
  const body = raw.startsWith('filter:') ? raw.substring('filter:'.length).trim() : raw
  if (!body) return null
  const parts = body.split(/\s*&&\s*/).map(s => s.trim()).filter(Boolean)
  const conds: FilterCond[] = []
  for (const p of parts) {
    const inMatch = p.match(/^(.*?)\s+in\s+(.+)$/i)
    if (inMatch) {
      let field = inMatch[1].trim()
      let rhsRaw = inMatch[2].trim()
      if (!field || !rhsRaw) return null
      if (field.startsWith('card.')) field = field.substring('card.'.length)
      if (!field.startsWith('content.')) field = `content.${field}`
      conds.push({ field, op: 'in', rhsRaw })
      continue
    }

    const cmpMatch = p.match(/^(.*?)\s*([=<>])\s*(.+)$/)
    if (cmpMatch) {
      let field = cmpMatch[1].trim()
      const opChar = cmpMatch[2] as '=' | '<' | '>'
      let rhsRaw = cmpMatch[3].trim()
      if (!field || !rhsRaw) return null
      if (field.startsWith('card.')) field = field.substring('card.'.length)
      if (!field.startsWith('content.')) field = `content.${field}`
      conds.push({ field, op: opChar, rhsRaw })
      continue
    }

    return null
  }
  return conds.length ? { conditions: conds } : null
}

function normalizeToStringArray(val: any): string[] {
  const flat: any[] = []
  const push = (x: any) => {
    if (x == null) return
    if (Array.isArray(x)) { x.forEach(push); return }
    flat.push(x)
  }
  push(val)
  const out: string[] = []
  for (const it of flat) {
    if (typeof it === 'string' || typeof it === 'number' || typeof it === 'boolean') {
      out.push(String(it))
      continue
    }
    if (typeof it === 'object') {
      const cand = (it as any).name ?? (it as any).title ?? (it as any).label ?? ((it as any).content?.name)
      if (cand != null) { out.push(String(cand)); continue }
    }
  }
  return Array.from(new Set(out.map(s => String(s))))
}

function parseMultiPathSpec(path?: string): { mode: 'single' | 'multi'; paths: string[] } {
  if (!path) return { mode: 'single', paths: [] }
  const trimmed = path.replace(/^\./, '')
  const m = trimmed.match(/^\{(.+)\}$/)
  if (m) {
    const raw = m[1]
    const parts = raw.split(',').map(s => s.trim()).filter(Boolean)
    return { mode: 'multi', paths: parts }
  }
  return { mode: 'single', paths: [trimmed] }
}

function pickFields(obj: any, paths: string[]): any {
  const out: Record<string, any> = {}
  for (const p of paths) {
    const val = getPathValue(obj, p)
    const key = p.split('.').pop() || p
    out[key] = val
  }
  return out
}

function getCurrentVolumeCard(cards: CardRead[], vars: ResolveVars): CardRead | undefined {
  if (typeof vars.volumeNumber !== 'number') return undefined
  const list = selectByType(cards, 'key:volume_outline')
  const sorted = [...list].sort((a, b) => {
    const na = extractVolumeNumberFromTitle(a.title)
    const nb = extractVolumeNumberFromTitle(b.title)
    if (na != null && nb != null) return na - nb
    return a.display_order - b.display_order
  })
  return sorted[vars.volumeNumber - 1]
}

function resolveCurrentStage(cards: CardRead[], vars: ResolveVars): any {
  const vol = getCurrentVolumeCard(cards, vars)
  const raw = (vol?.content as any) || {}
  const vo = unwrapVolumeOutline(raw)
  const stageLines = Array.isArray(vo?.stage_lines) ? vo.stage_lines : []
  if (!Array.isArray(stageLines) || stageLines.length === 0) return undefined
  const ch = Number(vars.chapterNumber)
  if (!Number.isFinite(ch)) return undefined
  return stageLines.find((s: any) => {
    const ref = s?.reference_chapter
    if (!Array.isArray(ref) || ref.length < 2) return false
    const start = Number(ref[0])
    const end = Number(ref[1])
    return Number.isFinite(start) && Number.isFinite(end) && ch >= start && ch <= end
  })
}

function resolvePreviousChapters(cards: CardRead[], vars: ResolveVars): any[] {
  const volNum = vars.volumeNumber
  const chNum = vars.chapterNumber
  if (typeof volNum !== 'number' || typeof chNum !== 'number') return []
  const chapterCards = selectByType(cards, 'key:chapter_outline')
  const filtered = chapterCards.filter(c => {
    const cc = c.content as any
    const vol = cc?.chapter_outline?.volume_number
    const cn = cc?.chapter_outline?.chapter_number
    return vol === volNum && typeof cn === 'number' && cn < chNum
  })
  return filtered
    .sort((a, b) => {
      const an = (a.content as any)?.chapter_outline?.chapter_number || 0
      const bn = (b.content as any)?.chapter_outline?.chapter_number || 0
      return an - bn
    })
    .map(c => {
      const cc = (c.content as any)?.chapter_outline || {}
      return {
        title: cc.title,
        chapter_number: cc.chapter_number,
        overview: cc.overview,
        enemy: cc.enemy || null,
        resolve_enemy: cc.resolve_enemy || null,
      }
    })
}

function resolveToken(rawToken: string, ctx: ResolveContext, vars: ResolveVars): string {
  // @self.parent.content

  const token = rawToken.replace(/^@/, '')

  const factsTokenValue = getFactsTokenValue(token, ctx)
  if (factsTokenValue !== undefined) {
    return stringifyValue(factsTokenValue)
  }

  const kgTokenValue = getKgTokenValue(token, ctx)
  if (kgTokenValue !== undefined) {
    return stringifyValue(kgTokenValue)
  }

  if (token.startsWith('stage:current')) {
    const path = token.includes('.') ? token.substring('stage:current.'.length) : ''
    const stage = resolveCurrentStage(ctx.cards, vars)
    const value = getPathValue(stage, path)
    return stringifyValue(value)
  }
  if (token === 'chapters:previous') {
    const arr = resolvePreviousChapters(ctx.cards, vars)
    return stringifyValue(arr)
  }

  const typeMatch = token.match(/^type:([^\.\[\s]+)(?:\[([^\]]+)\])?(?:\.(.+))?$/)
  if (typeMatch) {
    const typeName = typeMatch[1]
    const filter = typeMatch[2]
    const rawPath = typeMatch[3]
    const { mode: pathMode, paths: multiPaths } = parseMultiPathSpec(rawPath)

    const orderedAll = buildPreorder(ctx.cards)

    if (filter && filter.startsWith('previous')) {

      const parts = filter.split(':');
      let mode = 'global';
      let takeN: number | undefined = undefined;

      for (const part of parts.slice(1)) {
        if (part === 'global' || part === 'local') {
          mode = part;
        } else if (/^\d+$/.test(part)) {
          takeN = parseInt(part, 10);
        }
      }

      let prevList: CardRead[] = []

      if (mode === 'local') {
        const pid = ctx.currentCard?.parent_id ?? null
        const typeKey = resolveReferenceKey(typeName)
      const siblings = ctx.cards.filter(c =>
          c.parent_id === pid &&
          getCardTypeKey(c.card_type) === typeKey &&
          c.id !== ctx.currentCard?.id
        ).sort((a, b) => a.display_order - b.display_order)

        const currentIndex = siblings.findIndex(c => c.id === ctx.currentCard?.id)
        if (currentIndex > 0) {
          prevList = siblings.slice(0, currentIndex)
        }
        prevList = filterShortLivedEntityAcrossVolumes(ctx.cards, ctx.currentCard, prevList)
      } else {
        const indexById = new Map<number, number>()
        orderedAll.forEach((c, i) => indexById.set(c.id, i))
        const currentIndex = ctx.currentCard ? (indexById.get(ctx.currentCard.id) ?? -1) : -1
        const typeKey = resolveReferenceKey(typeName)
        prevList = orderedAll.filter((c, i) => getCardTypeKey(c.card_type) === typeKey && i < currentIndex)
        prevList = filterShortLivedEntityAcrossVolumes(ctx.cards, ctx.currentCard, prevList)

        if (typeof takeN === 'number' && takeN > 0 && prevList.length > takeN) {
          prevList = prevList.slice(-takeN)
        }
      }

      if (!rawPath) {
        const collected = prevList.map(c => getPathValue(c, 'content'))
        return stringifyValue(collected)
      }
      if (pathMode === 'multi') {
        const collected = prevList.map(c => pickFields(c, multiPaths))
        return stringifyValue(collected)
      } else {
        const collected = prevList.map(c => getPathValue(c, multiPaths[0]))
        return stringifyValue(collected)
      }
    }

    if (filter === 'sibling') {
      const pid = ctx.currentCard?.parent_id ?? null
      const typeKey = resolveReferenceKey(typeName)
      const siblings = ctx.cards.filter(c => c.parent_id === pid && getCardTypeKey(c.card_type) === typeKey && c.id !== ctx.currentCard?.id)
        .sort((a, b) => a.display_order - b.display_order)
      if (!rawPath) {
        const collected = siblings.map(c => getPathValue(c, 'content'))
        return stringifyValue(collected)
      }
      if (pathMode === 'multi') return stringifyValue(siblings.map(c => pickFields(c, multiPaths)))
      const collectedVals = siblings
        .map(c => getPathValue(c, multiPaths[0]))
        .filter(v => v !== undefined && v !== null && !(typeof v === 'string' && v.trim() === ''))
      if (collectedVals.length === 0) return ''
      if (collectedVals.length === 1) return stringifyValue(collectedVals[0])
      return stringifyValue(collectedVals)
    }

    const typeKey = resolveReferenceKey(typeName)
    const rawCandidates = orderedAll.filter(c => getCardTypeKey(c.card_type) === typeKey)
    let candidates = [...rawCandidates]
    candidates = candidates.sort((a, b) => {
      const na = extractVolumeNumberFromTitle(a.title)
      const nb = extractVolumeNumberFromTitle(b.title)
      if (na != null && nb != null) return na - nb
      return a.display_order - b.display_order
    })

    let selected: CardRead | undefined
    if (filter === 'last') selected = candidates[candidates.length - 1]
    else if (filter === 'first' || !filter) selected = candidates[0]
    else if (filter && filter.startsWith('index=')) {
      const expr = filter.substring('index='.length).trim()
      const f = parseFilterExpr(expr)
      if (f) {
        const matchFn = (card: CardRead) => {
          for (const cond of f.conditions) {
            let lv = getPathValue(card, cond.field)
            if ((cond.field.endsWith('.name') || cond.field === 'content.name') && (lv === undefined || lv === null || String(lv).trim() === '')) {
              lv = (card as any).title || (card as any)?.content?.title || ''
            }
            const lvStr = String(lv)
            if (cond.op === 'in') {
              const rhs = evalValueExpr(cond.rhsRaw, ctx, vars)
              const rhsArr = normalizeToStringArray(rhs)
              const setLower = new Set(rhsArr.map(x => String(x).toLowerCase()))
              if (!setLower.has(lvStr.toLowerCase())) return false
            } else if (cond.op === '=') {
              const rhs = evalValueExpr(cond.rhsRaw, ctx, vars)
              const rhsStr = String(Array.isArray(rhs) ? rhs[0] : rhs)
              const lvNum = Number(lvStr)
              const rhsNum = Number(rhsStr)
              if (Number.isFinite(lvNum) && Number.isFinite(rhsNum)) {
                if (lvNum !== rhsNum) return false
              } else {
                if (lvStr !== rhsStr) return false
              }
            } else if (cond.op === '<' || cond.op === '>') {
              const rhs = evalValueExpr(cond.rhsRaw, ctx, vars)
              const rhsStr = String(Array.isArray(rhs) ? rhs[0] : rhs)
              const a = Number(lvStr)
              const b = Number(rhsStr)
              if (Number.isFinite(a) && Number.isFinite(b)) {
                if (cond.op === '<' && !(a < b)) return false
                if (cond.op === '>' && !(a > b)) return false
              } else {
                const cmp = lvStr.localeCompare(rhsStr)
                if (cond.op === '<' && !(cmp < 0)) return false
                if (cond.op === '>' && !(cmp > 0)) return false
              }
            }
          }
          return true
        }
        const matched = candidates.filter(matchFn)
        if (!rawPath) {
          const collected = matched.map(c => getPathValue(c, 'content'))
          return stringifyValue(collected)
        }
        if (pathMode === 'multi') {
          const collected = matched.map(c => pickFields(c, multiPaths))
          return stringifyValue(collected)
        } else {
          const collected = matched.map(c => getPathValue(c, multiPaths[0]))
          return stringifyValue(collected)
        }
      }
      if (expr.startsWith('filter:')) {
        return ''
      }
      const idx = evalIndexExpr(expr, vars, ctx, candidates.length)
      if (idx === 'last') selected = candidates[candidates.length - 1]
      else if (typeof idx === 'number') {
        if (idx < 1 || idx > candidates.length) return ''
        selected = candidates[idx - 1]
      }
    }

    if (!selected) selected = candidates[0]

    if (!rawPath) {
      const value = getPathValue(selected, 'content')
      return stringifyValue(value)
    }
    if (pathMode === 'multi') {
      const obj = pickFields(selected, multiPaths)
      return stringifyValue(obj)
    } else {
      const value = getPathValue(selected, multiPaths[0])
      return stringifyValue(value)
    }
  }

  const selfMatch = token.match(/^self(?:\.(.+))?$/)
  if (selfMatch) {
    const raw = selfMatch[1]
    const { mode: pathMode, paths: multiPaths } = parseMultiPathSpec(raw)
    if (!raw) return stringifyValue(getPathValue(ctx.currentCard, 'content'))
    if (pathMode === 'multi') {
      const obj = pickFields(ctx.currentCard, multiPaths)
      return stringifyValue(obj)
    } else {
      const value = getPathValue(ctx.currentCard, multiPaths[0])
      return stringifyValue(value)
    }
  }
  const parentMatch = token.match(/^parent(?:\.(.+))?$/)
  if (parentMatch) {
    const raw = parentMatch[1]
    const parent = selectParent(ctx.cards, ctx.currentCard)
    const { mode: pathMode, paths: multiPaths } = parseMultiPathSpec(raw)
    if (!raw) return stringifyValue(getPathValue(parent, 'content'))
    if (pathMode === 'multi') {
      const obj = pickFields(parent, multiPaths)
      return stringifyValue(obj)
    } else {
      const value = getPathValue(parent, multiPaths[0])
      return stringifyValue(value)
    }
  }

  if (!token.startsWith('stage:') && !token.startsWith('chapters:')) {
    const titleMatch = token.match(/^([^\.\[\s]+)(?:\.(.+))?$/)
    if (titleMatch) {
      const title = titleMatch[1]
      const raw = titleMatch[2]
      const card = selectByTitle(ctx.cards, title)
      if (!raw) return stringifyValue(getPathValue(card, 'content'))
      const { mode: pathMode, paths: multiPaths } = parseMultiPathSpec(raw)
      if (pathMode === 'multi') {
        const obj = pickFields(card, multiPaths)
        return stringifyValue(obj)
      } else {
        const value = getPathValue(card, multiPaths[0])
        return stringifyValue(value)
      }
    }
  }

  return `[Error: Invalid reference '${rawToken}']`
}

export function resolveTemplate(ctx: ResolveContext): string {
  const vars = buildVars(ctx)
  const { template } = ctx
  if (!template) return ''

  const s = template
  const tokens: { start: number; end: number; raw: string }[] = []
  const n = s.length
  let i = 0
  while (i < n) {
    const at = s.indexOf('@', i)
    if (at === -1) break
    let j = at + 1
    let depthSquare = 0
    let depthCurly = 0
    let quote: '"' | "'" | null = null
    while (j < n) {
      const ch = s[j]
      const prev = j > 0 ? s[j - 1] : ''
      if (quote) {
        if (ch === quote && prev !== '\\') quote = null
        j++
        continue
      }
      if (ch === '"' || ch === "'") {
        quote = ch as any
        j++
        continue
      }
      if (ch === '[') { depthSquare++; j++; continue }
      if (ch === ']') { depthSquare = Math.max(0, depthSquare - 1); j++; continue }
      if (ch === '{') { depthCurly++; j++; continue }
      if (ch === '}') { depthCurly = Math.max(0, depthCurly - 1); j++; continue }
      if ((ch === '@' || /\s/.test(ch)) && depthSquare === 0 && depthCurly === 0) break
      j++
    }
    const raw = s.substring(at, j)
    tokens.push({ start: at, end: j, raw })
    i = j + 1
  }

  let result = s
  for (let k = tokens.length - 1; k >= 0; k--) {
    const t = tokens[k]
    const replacement = resolveToken(t.raw, ctx, vars)
    result = result.slice(0, t.start) + replacement + result.slice(t.end)
  }
  return result
}
