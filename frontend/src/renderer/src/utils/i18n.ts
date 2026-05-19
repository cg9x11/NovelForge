import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import { translateText } from '@renderer/locales/runtimeTranslations'

export function tr(text: string): string {
  const localeStore = useLocaleStore()
  return translateText(text, localeStore.locale)
}

