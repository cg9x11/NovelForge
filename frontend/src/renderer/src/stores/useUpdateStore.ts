import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ReleaseInfo, UpdateCheckResult } from '@renderer/services/updateService'
import { i18n } from '@renderer/i18n'
import { autoCheckForUpdates, manualCheckForUpdates, getCurrentVersion } from '@renderer/services/updateService'

export const useUpdateStore = defineStore('update', () => {
  const currentVersion = ref(getCurrentVersion())

  const latestVersion = ref<string | null>(null)
  const releaseInfo = ref<ReleaseInfo | null>(null)

  const hasUpdate = computed(() => {
    return latestVersion.value !== null && releaseInfo.value !== null
  })

  const isChecking = ref(false)
  const lastCheckTime = ref<Date | null>(null)
  const lastCheckError = ref<string | null>(null)

  const autoCheckEnabled = ref(true)

  const STORAGE_KEY = 'novelforge_auto_update_enabled'
  const storedSetting = localStorage.getItem(STORAGE_KEY)
  if (storedSetting !== null) {
    autoCheckEnabled.value = storedSetting === 'true'
  }

  function setAutoCheckEnabled(enabled: boolean) {
    autoCheckEnabled.value = enabled
    localStorage.setItem(STORAGE_KEY, String(enabled))
  }

  async function performCheck(checkFn: () => Promise<UpdateCheckResult>): Promise<UpdateCheckResult> {
    isChecking.value = true
    lastCheckError.value = null

    try {
      const result = await checkFn()

      lastCheckTime.value = new Date()

      if (result.hasUpdate && result.releaseInfo) {
        latestVersion.value = result.latestVersion || null
        releaseInfo.value = result.releaseInfo
      } else {
        latestVersion.value = null
        releaseInfo.value = null
      }

      return result
    } catch (error: any) {
      lastCheckError.value = error.message || String(i18n.global.t('update.errors.check_failed'))
      throw error
    } finally {
      isChecking.value = false
    }
  }

  async function autoCheck(): Promise<UpdateCheckResult> {
    return performCheck(autoCheckForUpdates)
  }

  async function manualCheck(): Promise<UpdateCheckResult> {
    return performCheck(manualCheckForUpdates)
  }

  function clearUpdateNotification() {
  }

  function clearError() {
    lastCheckError.value = null
  }

  return {
    currentVersion,
    latestVersion,
    releaseInfo,
    hasUpdate,
    isChecking,
    lastCheckTime,
    lastCheckError,
    autoCheckEnabled,

    autoCheck,
    manualCheck,
    setAutoCheckEnabled,
    clearUpdateNotification,
    clearError
  }
})
