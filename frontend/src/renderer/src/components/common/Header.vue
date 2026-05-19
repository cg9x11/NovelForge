<script setup lang="ts">
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Setting, Sunny, Moon, Document } from '@element-plus/icons-vue'
import { useAppStore } from '@renderer/stores/useAppStore'
import { useProjectStore } from '@renderer/stores/useProjectStore'
import { useUpdateStore } from '@renderer/stores/useUpdateStore'
import KnowledgeManager from '../setting/KnowledgeManager.vue'
import { useI18n } from 'vue-i18n'

const appStore = useAppStore()
const projectStore = useProjectStore()
const updateStore = useUpdateStore()
const { currentView, isDarkMode } = storeToRefs(appStore)
const { t } = useI18n()

function toggleTheme() {
  appStore.toggleTheme()
}

function openSettingsDialog() {
  appStore.openSettings()
}

function openWorkflowManager() {
  appStore.goToWorkflows()
  window.location.hash = '#/workflows'
}

function handleLogoClick() {
  if (currentView.value !== 'dashboard') {
    appStore.goToDashboard()
  }
}

const isLogoClickable = computed(() => currentView.value !== 'dashboard')

function openIdeasWorkbench() {
  // ç›´æŽ¥è°ƒç”¨ä¸»è¿›ç¨‹æ‰“å¼€æ–°çª—å£ï¼Œé¿å…å½“å‰çª—å£è·¯ç”±æˆ–çŠ¶æ€å˜åŒ–å¼•èµ·çš„é—ªçƒ
  // @ts-ignore
  appStore.goToIdeas()
  window.location.hash = '#/ideas-home'
}

// çŸ¥è¯†åº“æŠ½å±‰
// const kbVisible = ref(false)
</script>

<template>
  <header class="app-header">
    <div class="logo-container" @click="handleLogoClick" :class="{ clickable: isLogoClickable }">
      <span class="logo-text">Novel Forge</span>
    </div>
    <div class="actions-container">
      <el-button type="primary" :title="t('header.ideas')" @click="openIdeasWorkbench">
        <el-icon><Document /></el-icon>
        <span style="margin-left:6px;">{{ t('header.ideas') }}</span>
      </el-button>
      <el-button type="primary" plain :title="t('header.workflow')" @click="openWorkflowManager">{{ t('header.workflow') }}</el-button>
      <el-button :icon="isDarkMode ? Moon : Sunny" @click="toggleTheme" circle :title="t('header.toggle_theme')" />
      <el-badge :is-dot="updateStore.hasUpdate" type="warning">
        <el-button :icon="Setting" @click="openSettingsDialog" circle :title="t('header.settings')" />
      </el-badge>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  flex-shrink: 0; /* Prevent header from shrinking */
}

.logo-container.clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.logo-container.clickable:hover {
  opacity: 0.8;
}

.logo-container .logo-text {
  font-size: 20px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.actions-container {
  display: flex;
  gap: 15px;
}
</style> 

