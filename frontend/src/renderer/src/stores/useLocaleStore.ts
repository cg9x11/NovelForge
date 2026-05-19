import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type AppLocale = 'zh-CN' | 'en-US' | 'vi-VN'

const LOCALE_KEY = 'app-locale'

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<AppLocale>('zh-CN')

  const isChinese = computed(() => locale.value === 'zh-CN')
  const isEnglish = computed(() => locale.value === 'en-US')
  const isVietnamese = computed(() => locale.value === 'vi-VN')

  function initLocale() {
    const saved = localStorage.getItem(LOCALE_KEY) as AppLocale | null
    if (saved === 'zh-CN' || saved === 'en-US' || saved === 'vi-VN') {
      locale.value = saved
    }
  }

  function setLocale(next: AppLocale) {
    locale.value = next
    localStorage.setItem(LOCALE_KEY, next)
  }

  return {
    locale,
    isChinese,
    isEnglish,
    isVietnamese,
    initLocale,
    setLocale
  }
})

