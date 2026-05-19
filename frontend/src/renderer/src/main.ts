import './assets/main.css'

import { setupWebMock } from './web-mock'
setupWebMock()

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import { useAppStore } from './stores/useAppStore'
import { usePerCardAISettingsStore } from './stores/usePerCardAISettingsStore'
import { useLocaleStore } from './stores/useLocaleStore'
import { i18n } from './i18n'
import { installRuntimeTranslator } from './locales/runtimeTranslations'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(ElementPlus)
app.use(i18n)

// 初始化主题（必须在挂载前）
const appStore = useAppStore()
appStore.initTheme()

const localeStore = useLocaleStore()
localeStore.initLocale()
i18n.global.locale.value = localeStore.locale

// --- Load initial data ---
const perCardStore = usePerCardAISettingsStore()
perCardStore.loadFromLocal()

app.mount('#app')

installRuntimeTranslator(() => localeStore.locale)

localeStore.$subscribe((_mutation, state) => {
  i18n.global.locale.value = state.locale
})
