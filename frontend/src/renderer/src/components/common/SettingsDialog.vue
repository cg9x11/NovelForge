<script setup lang="ts">
import { computed, ref } from 'vue'
import LLMConfigManager from '../setting/LLMConfigManager.vue'
import Versions from '../Versions.vue'
import PromptWorkshop from '../setting/PromptWorkshop.vue'
import CardTypeManager from '../setting/CardTypeManager.vue'
import KnowledgeManager from '../setting/KnowledgeManager.vue'
import AssistantSettings from '../setting/AssistantSettings.vue'
import { useUpdateStore } from '@renderer/stores/useUpdateStore'
import { useLocaleStore, type AppLocale } from '@renderer/stores/useLocaleStore'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; 'close': [] }>()

const activeTab = ref('llm')
// 读取全局 store 预设的初始 tab
import { useAppStore } from '@renderer/stores/useAppStore'
const appStore = useAppStore()
const updateStore = useUpdateStore()
const localeStore = useLocaleStore()
const { t } = useI18n()
activeTab.value = appStore.settingsInitialTab || 'llm'

const currentLocale = computed({
  get: () => localeStore.locale,
  set: (value: AppLocale) => localeStore.setLocale(value)
})

function handleClose() {
  emit('update:modelValue', false)
  emit('close')
}

// 当切到 LLM 标签或首次显示时，让子组件刷新
import { onMounted, watch, nextTick } from 'vue'
const llmManagerRef = ref()
function emitRefreshIfLLM() {
  if (activeTab.value === 'llm' && llmManagerRef.value?.refresh) {
    llmManagerRef.value.refresh()
  }
}
onMounted(() => emitRefreshIfLLM())
watch(() => activeTab.value, () => emitRefreshIfLLM())
// 对话框每次打开也刷新一次（等待子组件渲染完成）
watch(() => props.modelValue, async (open) => { if (open) { await nextTick(); emitRefreshIfLLM() } })
</script>

<template>
  <el-dialog 
    :model-value="modelValue" 
    @update:model-value="(val) => emit('update:modelValue', val)"
    :title="t('app.settings')" 
    width="85%" 
    top="4vh"
    @close="handleClose"
  >
    <div class="settings-container">
      <el-tabs v-model="activeTab" tab-position="left" class="settings-tabs">
        <el-tab-pane :label="t('settingsDialog.tabs.llm')" name="llm">
          <LLMConfigManager ref="llmManagerRef" />
        </el-tab-pane>
        <el-tab-pane :label="t('settingsDialog.tabs.knowledge')" name="knowledge">
          <KnowledgeManager />
        </el-tab-pane>
        <el-tab-pane :label="t('settingsDialog.tabs.prompts')" name="prompts">
          <PromptWorkshop />
        </el-tab-pane>
        <el-tab-pane :label="t('settingsDialog.tabs.cardTypes')" name="card-types">
          <CardTypeManager />
        </el-tab-pane>
        <el-tab-pane :label="t('settingsDialog.tabs.assistant')" name="assistant">
          <AssistantSettings />
        </el-tab-pane>
        <el-tab-pane name="about">
          <template #label>
            <el-badge :is-dot="updateStore.hasUpdate" type="warning">
              <span>{{ t('settingsDialog.tabs.about') }}</span>
            </el-badge>
          </template>
          <div class="about-toolbar">
            <span class="locale-label">{{ t('app.language') }}</span>
            <el-select v-model="currentLocale" style="width: 200px">
              <el-option value="zh-CN" :label="t('app.language_zh')" />
              <el-option value="en-US" :label="t('app.language_en')" />
              <el-option value="vi-VN" :label="t('app.language_vi')" />
            </el-select>
          </div>
          <Versions />
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-dialog>
</template>

<style scoped>
.settings-container { height: 78vh; }
.about-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.locale-label { font-size: 13px; color: var(--el-text-color-regular); }
.settings-tabs { height: 100%; }
:deep(.el-dialog__body) { padding-top: 8px; }
:deep(.el-tabs__content) { height: 100%; overflow-y: auto; }
</style> 
