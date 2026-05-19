<script setup lang="ts">
import { computed } from 'vue'
import { useUpdateStore } from '@renderer/stores/useUpdateStore'
import { useLocaleStore, type AppLocale } from '@renderer/stores/useLocaleStore'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const updateStore = useUpdateStore()
const localeStore = useLocaleStore()

const currentLocale = computed({
  get: () => localeStore.locale,
  set: (value: AppLocale) => localeStore.setLocale(value)
})

const handleManualCheck = async () => {
  try {
    const result = await updateStore.manualCheck()
    if (result.hasUpdate) {
      ElMessage.success(t('versions.messages.new_version_found', { version: result.latestVersion }))
    } else {
      ElMessage.info(t('versions.messages.already_latest'))
    }
  } catch (error: any) {
    ElMessage.error(error.message || t('versions.messages.check_failed'))
  }
}

const handleAutoCheckToggle = (value: boolean) => {
  updateStore.setAutoCheckEnabled(value)
  ElMessage.success(value ? t('versions.messages.auto_check_enabled') : t('versions.messages.auto_check_disabled'))
}

const openReleasePage = () => {
  if (updateStore.releaseInfo?.htmlUrl) {
    window.open(updateStore.releaseInfo.htmlUrl, '_blank')
  }
}

const formatTime = (date: Date | null) => {
  if (!date) return t('versions.never_checked')
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
</script>

<template>
  <div class="about-page">
    <el-card shadow="never" class="version-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('versions.current_version') }}</span>
        </div>
      </template>
      <div class="version-info">
        <div class="version-number">{{ updateStore.currentVersion }}</div>
        <div class="version-meta">
          <div v-if="updateStore.lastCheckTime" class="last-check">
            {{ t('versions.last_checked') }}{{ formatTime(updateStore.lastCheckTime) }}
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="update-settings-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('versions.update_settings') }}</span>
        </div>
      </template>
      <div class="settings-row">
        <div class="setting-item">
          <span class="setting-label">{{ t('versions.auto_check_updates') }}</span>
          <el-switch :model-value="updateStore.autoCheckEnabled" @change="handleAutoCheckToggle" />
        </div>
        <div class="setting-item">
          <span class="setting-label">{{ t('versions.manual_check') }}</span>
          <el-button type="primary" :icon="Refresh" :loading="updateStore.isChecking" @click="handleManualCheck">
            {{ updateStore.isChecking ? t('versions.checking') : t('versions.check_updates') }}
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="language-settings-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('versions.system_settings') }}</span>
        </div>
      </template>
      <div class="setting-item language-setting-item">
        <span class="setting-label">{{ t('app.language') }}</span>
        <el-select v-model="currentLocale" style="width: 200px">
          <el-option value="zh-CN" :label="t('app.language_zh')" />
          <el-option value="en-US" :label="t('app.language_en')" />
          <el-option value="vi-VN" :label="t('app.language_vi')" />
        </el-select>
      </div>
    </el-card>

    <el-card v-if="updateStore.hasUpdate" shadow="never" class="new-version-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('versions.latest_release') }}</span>
          <el-tag type="warning" effect="dark">v{{ updateStore.latestVersion }}</el-tag>
        </div>
      </template>
      <div class="release-info">
        <div class="release-meta">
          <span class="release-name">{{ updateStore.releaseInfo?.name }}</span>
          <el-button type="primary" size="small" :icon="Download" @click="openReleasePage">
            {{ t('versions.view_details') }}
          </el-button>
        </div>
        <div class="release-notes">
          <div class="notes-title">{{ t('versions.release_notes') }}</div>
          <div class="notes-content">{{ updateStore.releaseInfo?.body || t('versions.no_release_notes') }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.about-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.version-card .version-info {
  text-align: center;
  padding: 20px 0;
}

.version-number {
  font-size: 48px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}

.version-meta {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.update-settings-card .settings-row {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.setting-item:last-child {
  border-bottom: none;
}

.language-setting-item {
  border-bottom: none;
}

.setting-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.new-version-card {
  border: 2px solid var(--el-color-warning);
}

.release-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.release-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.release-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.release-notes {
  background-color: var(--el-fill-color-lighter);
  border-radius: 6px;
  padding: 16px;
}

.notes-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--el-text-color-primary);
}

.notes-content {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  white-space: pre-line;
  max-height: 200px;
  overflow-y: auto;
  font-size: 14px;
}
</style>
