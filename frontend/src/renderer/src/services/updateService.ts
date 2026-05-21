import { i18n } from '@renderer/i18n'

export interface ReleaseInfo {
  version: string
  name: string
  body: string // Release notes (Markdown)
  publishedAt: string
  htmlUrl: string
  downloadUrl?: string
}

export interface UpdateCheckResult {
  hasUpdate: boolean
  currentVersion: string
  latestVersion?: string
  releaseInfo?: ReleaseInfo
}

const GITHUB_REPO = 'RhythmicWave/NovelForge'
const GITHUB_API_BASE = 'https://api.github.com'
const REQUEST_TIMEOUT = 10000

export function getCurrentVersion(): string {
  return import.meta.env.VITE_APP_VERSION || '0.8.5'
}

function compareVersions(v1: string, v2: string): number {
  const parseVersion = (v: string) => {
    const cleaned = v.replace(/^v/, '')
    const [core, suffixRaw] = cleaned.split('-', 2)
    const coreParts = core.split('.').map((s) => {
      const n = parseInt(s, 10)
      return Number.isNaN(n) ? 0 : n
    })
    return { coreParts, suffix: suffixRaw || '' }
  }

  const a = parseVersion(v1)
  const b = parseVersion(v2)

  const maxLen = Math.max(a.coreParts.length, b.coreParts.length)
  for (let i = 0; i < maxLen; i++) {
    const num1 = a.coreParts[i] ?? 0
    const num2 = b.coreParts[i] ?? 0
    if (num1 > num2) return 1
    if (num1 < num2) return -1
  }

  if (a.suffix === b.suffix) return 0
  if (a.suffix && !b.suffix) return 1
  if (!a.suffix && b.suffix) return -1

  const re = /^([a-zA-Z\-]*)(\d*)$/
  const ma = a.suffix.match(re)
  const mb = b.suffix.match(re)
  if (ma && mb) {
    const labelA = ma[1]
    const labelB = mb[1]
    const numA = ma[2] ? parseInt(ma[2], 10) : 0
    const numB = mb[2] ? parseInt(mb[2], 10) : 0
    if (labelA === labelB && (numA !== numB)) {
      return numA > numB ? 1 : -1
    }
  }

  if (a.suffix > b.suffix) return 1
  if (a.suffix < b.suffix) return -1
  return 0
}

async function fetchWithTimeout(url: string, timeout: number): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NovelForge-App'
      }
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    throw error
  }
}

async function fetchLatestRelease(timeout: number = REQUEST_TIMEOUT): Promise<ReleaseInfo> {
  const url = `${GITHUB_API_BASE}/repos/${GITHUB_REPO}/releases/latest`

  try {
    const response = await fetchWithTimeout(url, timeout)

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error(String(i18n.global.t('update.errors.github_rate_limited')))
      }
      throw new Error(String(i18n.global.t('update.errors.github_status', { status: response.status })))
    }

    const data = await response.json()

    return {
      version: data.tag_name?.replace(/^v/, '') || data.name,
      name: data.name || data.tag_name,
      body: data.body || '',
      publishedAt: data.published_at,
      htmlUrl: data.html_url,
      downloadUrl: data.assets?.[0]?.browser_download_url
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error(String(i18n.global.t('update.errors.timeout')))
    }
    throw error
  }
}

export async function checkForUpdates(maxRetries: number = 0): Promise<UpdateCheckResult> {
  const currentVersion = getCurrentVersion()
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const releaseInfo = await fetchLatestRelease()

      if (!releaseInfo) {
        return {
          hasUpdate: false,
          currentVersion
        }
      }

      const hasUpdate = compareVersions(releaseInfo.version, currentVersion) > 0

      return {
        hasUpdate,
        currentVersion,
        latestVersion: releaseInfo.version,
        releaseInfo: hasUpdate ? releaseInfo : undefined
      }
    } catch (error: any) {
      lastError = error

      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 2000 * (attempt + 1)))
      }
    }
  }

  throw lastError || new Error(String(i18n.global.t('update.errors.check_failed')))
}

export async function autoCheckForUpdates(): Promise<UpdateCheckResult> {
  return checkForUpdates(1)
}

export async function manualCheckForUpdates(): Promise<UpdateCheckResult> {
  return checkForUpdates(0)
}
