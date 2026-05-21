import { useLocaleStore } from '@renderer/stores/useLocaleStore'

export function tr(text: string): string {
  useLocaleStore()
  return text
}
