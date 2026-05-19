import type { AppLocale } from '@renderer/stores/useLocaleStore'
import enLocale from './en-US.json'
import viLocale from './vi-VN.json'

type TranslationMap = Record<string, string>
const CHINESE_RE = /[\u4e00-\u9fff]/
const RUNTIME_CACHE_KEY_PREFIX = 'runtime-translation-cache:'

const enUS: TranslationMap = {
  '应用设置': 'Settings',
  '语言': 'Language',
  'LLM 配置': 'LLM Configs',
  '知识库': 'Knowledge Base',
  '提示词工坊': 'Prompt Workshop',
  '卡片类型': 'Card Types',
  'Agent 设置': 'Agent Settings',
  '关于': 'About',
  '灵感助手': 'Idea Assistant',
  '新增对话': 'New Chat',
  '历史对话': 'Chat History',
  '刷新上下文': 'Refresh Context',
  '预览': 'Preview',
  '请输入你的需求，我会先给出建议。': 'Enter your request. I will suggest a plan first.',
  '正在生成中…': 'Generating…',
  '引用卡片': 'Referenced Cards',
  '个': '',
  '删除引用': 'Remove Reference',
  '添加引用': 'Add Reference',
  '选择模型': 'Select Model',
  '输入你的想法、约束或追问': 'Enter your idea, constraints, or follow-up',
  '添加引用卡片': 'Add Referenced Card',
  '来源项目': 'Source Project',
  '全部': 'All',
  '取消': 'Cancel',
  '确认': 'Confirm',
  '保存': 'Save',
  '删除': 'Delete',
  '编辑': 'Edit',
  '关闭': 'Close',
  '未设置': 'Not set',
  '新对话': 'New Chat',
  '已删除会话': 'Session deleted',
  '删除会话失败': 'Failed to delete session',
  '加载中...': 'Loading...',
  '加载中…': 'Loading…',
  '操作失败': 'Operation failed',
  '输入校验失败:': 'Input validation failed:',
  '发生了一个未知的校验错误': 'An unknown validation error occurred',
  '请求失败': 'Request failed',
  '请先设置有效的模型ID': 'Please set a valid model ID first',
  '未设置生成任务名（prompt）': 'Generation task name (prompt) is not set',
  '已保存到本卡片设置': 'Saved to current card settings',
  '保存失败': 'Save failed',
  '主题标签': 'Theme Tags',
  '请选择小说主题': 'Select novel themes',
  '已保存标签设置': 'Tag settings saved',
  '模型': 'Model',
  '名称：': 'Name:',
  '模型：': 'Model:',
  '⏳ 正在调用工具: ': '⏳ Calling tool: '
}

const viVN: TranslationMap = {
  '应用设置': 'Cài đặt',
  '语言': 'Ngôn ngữ',
  'LLM 配置': 'Cấu hình LLM',
  '知识库': 'Kho tri thức',
  '提示词工坊': 'Xưởng prompt',
  '卡片类型': 'Loại thẻ',
  'Agent 设置': 'Cài đặt Agent',
  '关于': 'Giới thiệu',
  '灵感助手': 'Trợ lý ý tưởng',
  '新增对话': 'Đoạn chat mới',
  '历史对话': 'Lịch sử chat',
  '刷新上下文': 'Làm mới ngữ cảnh',
  '预览': 'Xem trước',
  '请输入你的需求，我会先给出建议。': 'Nhập yêu cầu của bạn. Tôi sẽ đề xuất trước.',
  '正在生成中…': 'Đang tạo…',
  '引用卡片': 'Thẻ tham chiếu',
  '个': '',
  '删除引用': 'Xóa tham chiếu',
  '添加引用': 'Thêm tham chiếu',
  '选择模型': 'Chọn mô hình',
  '输入你的想法、约束或追问': 'Nhập ý tưởng, ràng buộc hoặc câu hỏi tiếp theo',
  '添加引用卡片': 'Thêm thẻ tham chiếu',
  '来源项目': 'Dự án nguồn',
  '全部': 'Tất cả',
  '取消': 'Hủy',
  '确认': 'Xác nhận',
  '保存': 'Lưu',
  '删除': 'Xóa',
  '编辑': 'Sửa',
  '关闭': 'Đóng',
  '未设置': 'Chưa đặt',
  '新对话': 'Chat mới',
  '已删除会话': 'Đã xóa phiên',
  '删除会话失败': 'Xóa phiên thất bại',
  '加载中...': 'Đang tải...',
  '加载中…': 'Đang tải…',
  '操作失败': 'Thao tác thất bại',
  '输入校验失败:': 'Kiểm tra dữ liệu thất bại:',
  '发生了一个未知的校验错误': 'Đã xảy ra lỗi kiểm tra không xác định',
  '请求失败': 'Yêu cầu thất bại',
  '请先设置有效的模型ID': 'Vui lòng đặt ID mô hình hợp lệ trước',
  '未设置生成任务名（prompt）': 'Chưa đặt tên tác vụ sinh nội dung (prompt)',
  '已保存到本卡片设置': 'Đã lưu vào cài đặt thẻ hiện tại',
  '保存失败': 'Lưu thất bại',
  '主题标签': 'Nhãn chủ đề',
  '请选择小说主题': 'Chọn chủ đề tiểu thuyết',
  '已保存标签设置': 'Đã lưu cài đặt nhãn',
  '模型': 'Mô hình',
  '名称：': 'Tên:',
  '模型：': 'Mô hình:',
  '⏳ 正在调用工具: ': '⏳ Đang gọi công cụ: '
}

const dictionaries: Record<AppLocale, TranslationMap> = {
  'zh-CN': {},
  'en-US': {
    ...(enLocale.runtime_translations as TranslationMap),
    ...enUS
  },
  'vi-VN': {
    ...(viLocale.runtime_translations as TranslationMap),
    ...viVN
  }
}

const pendingTranslations: Record<AppLocale, Set<string>> = {
  'zh-CN': new Set<string>(),
  'en-US': new Set<string>(),
  'vi-VN': new Set<string>()
}

let refreshTranslations: (() => void) | null = null

function loadRuntimeCache(locale: AppLocale) {
  if (locale === 'zh-CN') return
  try {
    const raw = localStorage.getItem(`${RUNTIME_CACHE_KEY_PREFIX}${locale}`)
    if (!raw) return
    const parsed = JSON.parse(raw) as TranslationMap
    Object.assign(dictionaries[locale], parsed)
  } catch {
  }
}

function persistRuntimeCache(locale: AppLocale) {
  if (locale === 'zh-CN') return
  try {
    localStorage.setItem(`${RUNTIME_CACHE_KEY_PREFIX}${locale}`, JSON.stringify(dictionaries[locale]))
  } catch {
  }
}

async function requestRemoteTranslation(text: string, locale: AppLocale): Promise<string | null> {
  if (locale === 'zh-CN') return text
  const target = locale === 'en-US' ? 'en' : 'vi'
  const langpair = `zh-CN|${target}`
  const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${encodeURIComponent(langpair)}`
  try {
    const response = await fetch(url)
    if (!response.ok) return null
    const data = await response.json() as { responseData?: { translatedText?: string } }
    const translated = data?.responseData?.translatedText?.trim()
    return translated || null
  } catch {
    return null
  }
}

function queueRuntimeTranslation(text: string, locale: AppLocale) {
  if (locale === 'zh-CN' || !CHINESE_RE.test(text)) return
  if (dictionaries[locale][text] || pendingTranslations[locale].has(text)) return

  pendingTranslations[locale].add(text)
  void requestRemoteTranslation(text, locale)
    .then((translated) => {
      if (translated && translated !== text) {
        dictionaries[locale][text] = translated
        persistRuntimeCache(locale)
        sortedEntries[locale] = Object.entries(dictionaries[locale])
          .filter(([key, value]) => key && value && key !== value)
          .sort((a, b) => b[0].length - a[0].length)
        refreshTranslations?.()
      }
    })
    .finally(() => {
      pendingTranslations[locale].delete(text)
    })
}

const sortedEntries: Record<AppLocale, Array<[string, string]>> = {
  'zh-CN': [],
  'en-US': [],
  'vi-VN': []
}

for (const locale of ['en-US', 'vi-VN'] as const) {
  sortedEntries[locale] = Object.entries(dictionaries[locale])
    .filter(([key, value]) => key && value && key !== value)
    .sort((a, b) => b[0].length - a[0].length)
}

export function translateText(raw: string, locale: AppLocale): string {
  if (!raw || locale === 'zh-CN') return raw
  const normalized = raw.trim()
  const dict = dictionaries[locale]
  if (dict[normalized]) return dict[normalized]

  let translated = raw
  for (const [source, target] of sortedEntries[locale]) {
    if (translated.includes(source)) {
      translated = translated.split(source).join(target)
    }
  }
  if (translated === raw && CHINESE_RE.test(normalized)) {
    queueRuntimeTranslation(normalized, locale)
  }
  return translated
}

function translateNodeText(node: Node, locale: AppLocale) {
  if (node.nodeType !== Node.TEXT_NODE) return
  const original = node.textContent || ''
  if (!original.trim()) return
  const translated = translateText(original, locale)
  if (translated !== original) {
    node.textContent = original.replace(original.trim(), translated)
  }
}

function translateAttributes(el: Element, locale: AppLocale) {
  for (const attr of ['placeholder', 'title', 'aria-label']) {
    const value = el.getAttribute(attr)
    if (!value) continue
    const translated = translateText(value, locale)
    if (translated !== value) el.setAttribute(attr, translated)
  }
}

function walk(root: Node, locale: AppLocale) {
  translateNodeText(root, locale)
  if (root instanceof Element) translateAttributes(root, locale)
  for (const child of Array.from(root.childNodes)) {
    walk(child, locale)
  }
}

let observer: MutationObserver | null = null
let applyTimer: number | null = null

export function installRuntimeTranslator(getLocale: () => AppLocale) {
  loadRuntimeCache('en-US')
  loadRuntimeCache('vi-VN')
  const apply = () => {
    observer?.disconnect()
    walk(document.body, getLocale())
    observer?.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['placeholder', 'title', 'aria-label']
    })
  }
  const scheduleApply = () => {
    if (applyTimer !== null) {
      window.clearTimeout(applyTimer)
    }
    applyTimer = window.setTimeout(() => {
      applyTimer = null
      apply()
    }, 80)
  }
  refreshTranslations = apply

  observer?.disconnect()
  observer = new MutationObserver(() => scheduleApply())
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['placeholder', 'title', 'aria-label']
  })

  apply()
  return apply
}
