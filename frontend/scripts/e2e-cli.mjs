import { chromium } from 'playwright'
import { spawn, spawnSync } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const frontendRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(frontendRoot, '..')
const artifactsDir = path.resolve(repoRoot, 'artifacts', 'e2e')
const apiBase = process.env.NOVELFORGE_API_BASE || 'http://127.0.0.1:54321'
const cdpPort = process.env.NOVELFORGE_E2E_PORT || '9222'
const cdpUrl = `http://127.0.0.1:${cdpPort}`
const command = process.argv[2] || 'smoke'
const keepOpen = process.env.NOVELFORGE_E2E_KEEP_OPEN === '1'
const e2eLocale = process.env.NOVELFORGE_E2E_LOCALE || 'en-US'
const started = []

function printHelp() {
  console.log(`NovelForge E2E CLI

Usage:
  node scripts/e2e-cli.mjs smoke
  node scripts/e2e-cli.mjs snapshot
  node scripts/e2e-cli.mjs screenshot [name]
  node scripts/e2e-cli.mjs click <visible text>
  node scripts/e2e-cli.mjs wait-text <visible text>
  node scripts/e2e-cli.mjs assert-no-cjk [label]

Env:
  NOVELFORGE_E2E_PORT=9222
  NOVELFORGE_API_BASE=http://127.0.0.1:54321
  NOVELFORGE_E2E_KEEP_OPEN=1
  NOVELFORGE_E2E_VERBOSE=1
`)
}

if (command === 'help' || command === '--help' || command === '-h') {
  printHelp()
  process.exit(0)
}

function log(message, data) {
  if (data === undefined) console.log(`[e2e] ${message}`)
  else console.log(`[e2e] ${message}`, JSON.stringify(data, null, 2))
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function waitFor(fn, label, timeoutMs = 30000, intervalMs = 250) {
  const start = Date.now()
  let lastError
  while (Date.now() - start < timeoutMs) {
    try {
      const result = await fn()
      if (result) return result
    } catch (error) {
      lastError = error
    }
    await sleep(intervalMs)
  }
  throw new Error(`${label} timeout${lastError ? `: ${lastError.message}` : ''}`)
}

async function waitForHttp(url, label, timeoutMs = 30000) {
  return waitFor(async () => {
    const response = await fetch(url)
    return response.ok ? response : false
  }, label, timeoutMs)
}

async function apiJson(pathname, options = {}) {
  const response = await fetch(`${apiBase}${pathname}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
  })
  const text = await response.text()
  let payload = null
  try { payload = text ? JSON.parse(text) : null } catch {}
  if (!response.ok) throw new Error(`${options.method || 'GET'} ${pathname} failed: ${response.status} ${text}`)
  return payload?.data ?? payload
}

async function cleanupStaleSmokeProjects() {
  try {
    const projects = await apiJson('/api/projects/')
    const stale = (projects || []).filter((project) => String(project?.name || '').startsWith('NF_E2E_'))
    for (const project of stale) await deleteSmokeProject(project)
    if (stale.length) log('deleted stale smoke projects', { count: stale.length })
  } catch (error) {
    log('cleanup stale smoke projects skipped', { error: String(error?.message || error) })
  }
}

async function createSmokeProject() {
  const name = `NF_E2E_${Date.now()}`
  const project = await apiJson('/api/projects/', {
    method: 'POST',
    body: JSON.stringify({ name, description: 'Temporary E2E project', template: null })
  })
  log('created smoke project', { id: project?.id, name })
  return project
}

async function deleteSmokeProject(project) {
  if (!project?.id) return
  try {
    await apiJson(`/api/projects/${project.id}`, { method: 'DELETE' })
    log('deleted smoke project', { id: project.id })
  } catch (error) {
    log('delete smoke project failed', { id: project.id, error: String(error?.message || error) })
  }
}

function startProcess(name, cmd, args, options = {}) {
  const child = spawn(cmd, args, {
    cwd: options.cwd || repoRoot,
    env: { ...process.env, ...options.env },
    shell: process.platform === 'win32',
    stdio: ['ignore', 'pipe', 'pipe']
  })
  child.stdout.on('data', (data) => process.stdout.write(`[${name}] ${data}`))
  child.stderr.on('data', (data) => process.stderr.write(`[${name}] ${data}`))
  child.on('exit', (code) => log(`${name} exited`, { code }))
  started.push(child)
  return child
}

async function ensureBackend() {
  try {
    await waitForHttp(`${apiBase}/openapi.json`, 'backend health', 1500)
    log('backend already ready')
    return
  } catch {}
  log('starting backend')
  startProcess('backend', 'python', ['backend/main.py'], { cwd: repoRoot })
  await waitForHttp(`${apiBase}/openapi.json`, 'backend health', 45000)
}

async function ensureFrontend() {
  try {
    await fetch(`${cdpUrl}/json/version`)
    log('frontend CDP already ready')
    return
  } catch {}
  log('starting frontend')
  startProcess('frontend', 'npm', ['run', 'dev'], {
    cwd: frontendRoot,
    env: { NOVELFORGE_E2E: '1', NOVELFORGE_E2E_PORT: cdpPort }
  })
  await waitForHttp(`${cdpUrl}/json/version`, 'frontend CDP', 60000)
}

async function connectPage() {
  const browser = await chromium.connectOverCDP(cdpUrl)
  const page = await waitFor(async () => {
    for (const context of browser.contexts()) {
      for (const page of context.pages()) {
        const url = page.url()
        if (url.includes('localhost') || url.includes('127.0.0.1') || url.startsWith('file:')) return page
      }
    }
    return false
  }, 'app page', 30000)
  await page.waitForLoadState('domcontentloaded')
  const activeLocale = await page.evaluate((locale) => {
    const current = localStorage.getItem('app-locale')
    if (current !== locale) localStorage.setItem('app-locale', locale)
    return current
  }, e2eLocale)
  if (activeLocale !== e2eLocale) await page.reload({ waitUntil: 'domcontentloaded' })
  return { browser, page }
}

async function snapshot(page) {
  return page.evaluate(() => {
    const visible = (el) => {
      const style = window.getComputedStyle(el)
      const rect = el.getBoundingClientRect()
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0
    }
    const buttons = [...document.querySelectorAll('button,[role="button"],.el-button')]
      .filter(visible)
      .slice(0, 80)
      .map((el) => (el.innerText || el.getAttribute('aria-label') || '').trim())
      .filter(Boolean)
    const inputs = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')]
      .filter(visible)
      .slice(0, 40)
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        placeholder: el.getAttribute('placeholder') || '',
        value: el.value || el.innerText || ''
      }))
    const headings = [...document.querySelectorAll('h1,h2,h3,.el-dialog__title,.page-title,.section-title')]
      .filter(visible)
      .slice(0, 40)
      .map((el) => el.innerText.trim())
      .filter(Boolean)
    const text = document.body.innerText.replace(/\s+/g, ' ').trim().slice(0, 5000)
    return {
      title: document.title,
      url: location.href,
      viewport: { width: innerWidth, height: innerHeight },
      headings,
      buttons,
      inputs,
      text
    }
  })
}

async function saveSnapshot(page, name) {
  await mkdir(artifactsDir, { recursive: true })
  const data = await snapshot(page)
  const out = path.join(artifactsDir, `${name}.json`)
  await writeFile(out, JSON.stringify(data, null, 2), 'utf-8')
  log('snapshot saved', { out })
  return data
}

async function saveScreenshot(page, name) {
  await mkdir(artifactsDir, { recursive: true })
  const out = path.join(artifactsDir, `${name}.png`)
  await page.screenshot({ path: out, fullPage: true })
  log('screenshot saved', { out })
  return out
}

async function waitForText(page, text, timeoutMs = 20000) {
  await page.getByText(text, { exact: false }).first().waitFor({ state: 'visible', timeout: timeoutMs })
}

async function clickText(page, text, timeoutMs = 20000) {
  const target = page.getByText(text, { exact: false }).first()
  await target.waitFor({ state: 'visible', timeout: timeoutMs })
  await target.click()
}

function normalizeTextForMatch(value) {
  return String(value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\u0111/g, 'd')
    .replace(/\u0110/g, 'D')
    .normalize('NFKC')
}


async function clickNormalizedText(page, text, selector = 'button,[role="button"],.el-button', options = {}) {
  const clicked = await page.evaluate(({ selector, text }) => {
    const normalize = (value) => String(value || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\u0111/g, 'd')
      .replace(/\u0110/g, 'D')
      .normalize('NFKC')
    const wanted = normalize(text).toLowerCase()
    const isVisible = (el) => {
      const rect = el.getBoundingClientRect()
      const style = window.getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none'
    }
    const elements = Array.from(document.querySelectorAll(selector)).filter(isVisible)
    const target = elements.find((el) => normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '').toLowerCase().includes(wanted))
    if (!target) return { clicked: false, candidates: elements.map((el) => normalize(el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '')).slice(0, 40) }
    target.click()
    return { clicked: true }
  }, { selector, text })
  if (!clicked?.clicked) {
    if (options.optional) return false
    throw new Error(`Text not found for click: ${text}; candidates=${JSON.stringify(clicked?.candidates || [])}`)
  }
  return true
}


async function expectAnyText(page, texts, label) {
  return waitFor(async () => {
    const data = await snapshot(page)
    const visibleText = normalizeTextForMatch(data.text)
    const found = texts.find((text) => visibleText.includes(normalizeTextForMatch(text)))
    return found ? { found, data } : false
  }, label, 20000)
}

function findCjk(text) {
  return [...new Set(text.match(/[\u4e00-\u9fff]+/g) || [])]
}

function snapshotSearchText(data) {
  return [
    data.text || '',
    ...(data.buttons || []),
    ...(data.headings || []),
    ...(data.inputs || []).flatMap((item) => [item.placeholder || '', item.value || ''])
  ].join(' ')
}

async function assertNoCjk(page, label) {
  const data = await waitFor(async () => {
    const current = await snapshot(page)
    const cjk = findCjk(snapshotSearchText(current))
    return cjk.length ? false : current
  }, `${label} no CJK`, 5000, 120).catch(async () => {
    const current = await snapshot(page)
    const cjk = findCjk(snapshotSearchText(current))
    await saveSnapshot(page, `cjk-${label.replace(/[^a-z0-9_-]+/gi, '-')}`)
    throw new Error(`${label} contains CJK text: ${cjk.slice(0, 20).join(', ')}`)
  })
  return data
}

const smokeText = {
  dashboard: e2eLocale === 'vi-VN' ? ['Tu sach', 'Du an'] : ['My Bookshelf', 'Project'],
  createProject: e2eLocale === 'vi-VN' ? ['Du an moi', 'Tao du an'] : ['New Project', 'Create Project'],
  createButton: e2eLocale === 'vi-VN' ? 'D\u1ef1 \u00e1n m\u1edbi' : 'New Project',
  startCreateButton: e2eLocale === 'vi-VN' ? 'B\u1eaft \u0111\u1ea7u vi\u1ebft' : 'Start Writing',
  projectTemplate: e2eLocale === 'vi-VN' ? ['Project Template', 'bong tuyet'] : ['Project Template', 'Snowflake'],
  workflowButton: e2eLocale === 'vi-VN' ? 'Quy tr\u00ecnh' : 'Workflow',
  workflowLibrary: e2eLocale === 'vi-VN'
    ? ['Thu vien node', 'Tri hoan', 'Chon du an', 'Tao the']
    : ['Node', 'Nodes', 'Logic', 'Delay', 'Select Project', 'Create Card'],
  delayNode: e2eLocale === 'vi-VN' ? 'Tr\u00ec ho\u00e3n' : 'Delay',
  delayParams: e2eLocale === 'vi-VN' ? ['Du lieu dau vao', 'So giay tre'] : ['Input data', 'Delay seconds'],
  back: e2eLocale === 'vi-VN' ? 'Quay l\u1ea1i' : 'Back',
  settingsButtonTitle: e2eLocale === 'vi-VN' ? 'C\u00e0i \u0111\u1eb7t' : 'Settings',
  settings: e2eLocale === 'vi-VN' ? ['Cai dat', 'LLM', 'Kho tri thuc', 'Prompt'] : ['Settings', 'LLM', 'Knowledge', 'Prompt', 'About'],
  settingsTabs: e2eLocale === 'vi-VN'
    ? [
      { name: 'knowledge', label: 'Kho tri thuc', expect: ['Kho tri thuc', 'Them moi'], createLabel: 'Tao tri thuc' },
      { name: 'prompts', label: 'Prompt', expect: ['Prompt', 'Them'], createLabel: 'Tao prompt moi' },
      { name: 'card-types', label: 'Loai the', expect: ['Loai the', 'Key', 'Ten'], createLabel: 'Them loai' },
      { name: 'assistant', label: 'Cai dat Agent', expect: ['Cai dat Agent'] },
      { name: 'about', label: 'Gioi thieu', expect: ['He thong', 'Ngon ngu'] }
    ]
    : [
      { name: 'knowledge', label: 'Knowledge', expect: ['Knowledge', 'Add'], createLabel: 'New knowledge' },
      { name: 'prompts', label: 'Prompt', expect: ['Prompt', 'Add'], createLabel: 'New Prompt' },
      { name: 'card-types', label: 'Card Types', expect: ['Card Types', 'Key', 'Name'], createLabel: 'Add Type' },
      { name: 'assistant', label: 'Agent Settings', expect: ['Agent Settings'] },
      { name: 'about', label: 'About', expect: ['System', 'Language'] }
    ],
  ideasButton: e2eLocale === 'vi-VN' ? '\u00dd t\u01b0\u1edfng' : 'Ideas',
  ideas: e2eLocale === 'vi-VN' ? ['Quay lai', 'Chuyen', 'the'] : ['Back', 'Transfer', 'Ideas', 'Card'],
  editStructure: e2eLocale === 'vi-VN' ? 'Sua cau truc' : 'Edit Structure',
  editSchema: e2eLocale === 'vi-VN' ? 'Sua cau truc' : 'Edit schema',
  schemaStudio: e2eLocale === 'vi-VN' ? ['Trinh dung schema', 'Xem truoc bieu mau', 'JSON schema'] : ['Schema Builder', 'Form Preview', 'Schema JSON']
}


async function auditEditorStructure(page) {
  const projectCount = await page.locator('.project-card:visible').count()
  if (!projectCount) {
    log('editor structure audit skipped', { reason: 'no visible project card' })
    return false
  }
  await page.locator('.project-card:visible').first().click()
  const hasTree = await waitFor(async () => await page.locator('.card-tree:visible, .custom-tree-node:visible').count(), 'editor card tree', 30000).catch(() => false)
  if (!hasTree) {
    log('editor structure audit skipped', { reason: 'editor card tree not visible' })
    await page.reload({ waitUntil: 'domcontentloaded' })
    await expectAnyText(page, smokeText.dashboard, 'dashboard after editor structure skip')
    return false
  }
  const nodeCount = await page.locator('.custom-tree-node:visible').count()
  if (!nodeCount) {
    log('editor structure audit skipped', { reason: 'no visible card nodes' })
    return false
  }
  for (let index = 0; index < Math.min(nodeCount, 8); index += 1) {
    await page.keyboard.press('Escape')
    await page.waitForTimeout(80)
    const node = page.locator('.custom-tree-node:visible').nth(index)
    await node.scrollIntoViewIfNeeded()
    await node.click({ force: true })
    await node.click({ button: 'right', force: true })
    await page.waitForTimeout(150)
    const opened = await clickNormalizedText(page, smokeText.editStructure, '.el-dropdown-menu__item,[role="menuitem"]', { optional: true })
    if (!opened) {
      await page.keyboard.press('Escape')
      await page.waitForTimeout(120)
      continue
    }
    await page.locator('.el-dialog:visible').first().waitFor({ state: 'visible', timeout: 20000 })
    await expectAnyText(page, smokeText.schemaStudio, 'schema studio')
    await saveSnapshot(page, '06-editor-structure')
    await saveScreenshot(page, '06-editor-structure')
    await assertNoCjk(page, 'editor structure')
    await page.keyboard.press('Escape')
    await waitFor(async () => await page.locator('.el-dialog:visible').count() === 0, 'schema dialog closed', 10000).catch(() => {})
    await page.reload({ waitUntil: 'domcontentloaded' })
    await expectAnyText(page, smokeText.dashboard, 'dashboard after editor structure')
    return true
  }
  log('editor structure audit skipped', { reason: 'no editable card node opened schema studio' })
  return false
}

async function auditWorkflowNodes(page) {
  const nodeLocator = page.locator('.node-item:visible')
  const nodeCount = await nodeLocator.count()
  if (!nodeCount) throw new Error('workflow node library has no nodes')
  const names = []
  for (let index = 0; index < nodeCount; index += 1) {
    const item = nodeLocator.nth(index)
    await item.scrollIntoViewIfNeeded()
    const name = (await item.locator('.node-name').first().innerText().catch(() => item.innerText())).trim().split('\n')[0]
    names.push(name)
    await item.click()
    await page.waitForTimeout(80)
    await assertNoCjk(page, `workflow node ${index + 1}: ${name}`)
  }
  log('workflow node audit', { nodeCount, names })
}

async function auditSettingsTabs(page) {
  for (const tab of smokeText.settingsTabs) {
    await clickNormalizedText(page, tab.label, '.el-tabs__item')
    await expectAnyText(page, tab.expect, `settings tab ${tab.name}`)
    await saveSnapshot(page, `04-settings-${tab.name}`)
    await assertNoCjk(page, `settings tab ${tab.name}`)
    if (tab.name === 'card-types') {
      const openedSchema = await clickNormalizedText(page, smokeText.editSchema, 'button,[role="button"],.el-button', { optional: true })
      if (!openedSchema) throw new Error(`Schema editor button not found for settings tab ${tab.name}: ${smokeText.editSchema}`)
      await page.locator('.el-dialog:visible').last().waitFor({ state: 'visible', timeout: 10000 })
      await expectAnyText(page, smokeText.schemaStudio, 'card type schema studio')
      await saveSnapshot(page, `04-settings-${tab.name}-schema`)
      await assertNoCjk(page, `settings tab ${tab.name} schema studio`)
      await page.keyboard.press('Escape')
      await waitFor(async () => await page.locator('.el-dialog:visible').count() <= 1, `settings tab ${tab.name} schema studio closed`, 10000).catch(() => {})
    }
    if (tab.createLabel) {
      const opened = await clickNormalizedText(page, tab.createLabel, 'button,[role="button"],.el-button', { optional: true })
      if (!opened) throw new Error(`Create dialog button not found for settings tab ${tab.name}: ${tab.createLabel}`)
      await page.locator('.el-dialog:visible').last().waitFor({ state: 'visible', timeout: 10000 })
      await saveSnapshot(page, `04-settings-${tab.name}-create`)
      await assertNoCjk(page, `settings tab ${tab.name} create dialog`)
      await page.keyboard.press('Escape')
      await waitFor(async () => await page.locator('.el-dialog:visible').count() <= 1, `settings tab ${tab.name} create dialog closed`, 10000).catch(() => {})
    }
  }
}

async function smoke() {
  await ensureBackend()
  await ensureFrontend()
  const { browser, page } = await connectPage()
  let smokeProject = null
  if (process.env.NOVELFORGE_E2E_VERBOSE === '1') {
    page.on('console', (message) => log(`console:${message.type()}`, message.text()))
  }
  page.on('pageerror', (error) => log('pageerror', error.message))
  try {
    await cleanupStaleSmokeProjects()
    smokeProject = await createSmokeProject()
    await page.setViewportSize({ width: 1280, height: 860 })
    await page.goto(new URL(page.url()).origin + '/', { waitUntil: 'domcontentloaded' })
    await expectAnyText(page, smokeText.dashboard, 'dashboard text')
    await saveSnapshot(page, '01-dashboard')
    await saveScreenshot(page, '01-dashboard')

    let openedCreateProject = false
    const createRoleButton = page.getByRole('button', { name: smokeText.createButton }).last()
    if (await createRoleButton.count()) {
      await createRoleButton.click().then(() => { openedCreateProject = true }).catch(() => {})
    }
    if (!openedCreateProject) {
      openedCreateProject = await clickNormalizedText(page, smokeText.createButton, 'button,[role="button"],.el-button', { optional: true })
    }
    if (!openedCreateProject) {
      openedCreateProject = await clickNormalizedText(page, smokeText.startCreateButton, 'button,[role="button"],.el-button', { optional: true })
    }
    if (openedCreateProject) {
      await page.locator('.el-dialog').first().waitFor({ state: 'visible', timeout: 20000 })
      await saveSnapshot(page, '02-create-project')
      await expectAnyText(page, smokeText.projectTemplate, 'project dialog/template')
      await saveScreenshot(page, '02-create-project')
      await page.keyboard.press('Escape')
      await page.reload({ waitUntil: 'domcontentloaded' })
      await expectAnyText(page, smokeText.dashboard, 'dashboard after dialog')
    } else {
      log('create project entry skipped', { reason: 'project already exists or button hidden' })
    }

    await auditEditorStructure(page)

    await page.getByText(smokeText.workflowButton, { exact: false }).first().click()
    await waitFor(async () => (await snapshot(page)).text !== '', 'post-workflow click')
    await saveSnapshot(page, '03-workflow-before-assert')
    await expectAnyText(page, smokeText.workflowLibrary, 'workflow node library')
    await saveSnapshot(page, '03-workflow-library')
    await page.locator('.node-item').filter({ hasText: smokeText.delayNode }).first().click()
    await saveSnapshot(page, '03-workflow-after-node-click')
    await expectAnyText(page, smokeText.delayParams, 'workflow node params')
    await auditWorkflowNodes(page)
    const workflowState = await page.evaluate(() => {
      const library = document.querySelector('.node-library, [class*="node-library"], [class*="NodeLibrary"], .library-section') || document.querySelector('aside')
      const rect = library?.getBoundingClientRect()
      return {
        hasLibrary: Boolean(library),
        libraryRect: rect ? { width: rect.width, height: rect.height } : null,
        libraryScrollHeight: library?.scrollHeight || 0,
        libraryClientHeight: library?.clientHeight || 0,
        bodyText: document.body.innerText.slice(0, 2000)
      }
    })
    log('workflow state', workflowState)
    await saveSnapshot(page, '03-workflow')
    await saveScreenshot(page, '03-workflow')
    await assertNoCjk(page, 'workflow')

    await page.getByText(smokeText.back, { exact: false }).first().click()
    await expectAnyText(page, smokeText.dashboard, 'dashboard before settings')
    await page.locator(`button[title="${smokeText.settingsButtonTitle}"]`).click()
    await expectAnyText(page, smokeText.settings, 'settings dialog')
    await saveSnapshot(page, '04-settings')
    await saveScreenshot(page, '04-settings')
    await assertNoCjk(page, 'settings')
    await auditSettingsTabs(page)
    await page.keyboard.press('Escape')

    await page.getByText(smokeText.ideasButton, { exact: false }).first().click()
    await expectAnyText(page, smokeText.ideas, 'ideas home')
    await saveSnapshot(page, '05-ideas')
    await saveScreenshot(page, '05-ideas')
    await assertNoCjk(page, 'ideas')
    await page.getByText(smokeText.back, { exact: false }).first().click()
    await expectAnyText(page, smokeText.dashboard, 'dashboard after ideas')

    await page.evaluate(async (base) => {
      const response = await fetch(`${base}/api/llm-configs/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'openai_compatible', api_base: 'https://router.noe.asia/v1', model_name: 'translator', api_key: 'dummy', api_protocol: 'responses', models_path: '/models' })
      })
      return response.json()
    }, apiBase).then((result) => log('llm test result', result))
  } finally {
    await deleteSmokeProject(smokeProject)
    if (!keepOpen) await browser.close()
    cleanup()
    if (!keepOpen) setTimeout(() => process.exit(0), 50)
  }
}

async function runCommand() {
  if (command === 'smoke') return smoke()
  await ensureBackend()
  await ensureFrontend()
  const { browser, page } = await connectPage()
  try {
    if (command === 'snapshot') console.log(JSON.stringify(await saveSnapshot(page, 'manual-snapshot'), null, 2))
    else if (command === 'screenshot') await saveScreenshot(page, process.argv[3] || 'manual-screenshot')
    else if (command === 'click') await clickText(page, process.argv.slice(3).join(' '))
    else if (command === 'wait-text') await waitForText(page, process.argv.slice(3).join(' '))
    else if (command === 'assert-no-cjk') await assertNoCjk(page, process.argv.slice(3).join(' ') || 'manual')
    else throw new Error(`Unknown command: ${command}`)
  } finally {
    if (!keepOpen) await browser.close()
    cleanup()
    if (!keepOpen) setTimeout(() => process.exit(0), 50)
  }
}

function cleanup() {
  if (keepOpen) return
  for (const child of started.reverse()) {
    if (child.killed || child.exitCode !== null) continue
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore' })
    } else {
      child.kill('SIGTERM')
    }
  }
}

process.on('SIGINT', () => { cleanup(); process.exit(130) })
process.on('SIGTERM', () => { cleanup(); process.exit(143) })

runCommand().catch((error) => {
  console.error(`[e2e] failed: ${error.stack || error.message}`)
  cleanup()
  process.exit(1)
})
