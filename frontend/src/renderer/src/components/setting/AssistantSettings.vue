<script setup lang="ts">
import { computed } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useAssistantPreferences } from '@renderer/composables/useAssistantPreferences'

const { t } = useI18n()
const prefs = useAssistantPreferences()

const ctxSummaryEnabled = computed({
  get: () => prefs.contextSummaryEnabled.value,
  set: (val: boolean) => prefs.setContextSummaryEnabled(val)
})

const ctxSummaryThreshold = computed({
  get: () => prefs.contextSummaryThreshold.value,
  set: (val: number | null) => prefs.setContextSummaryThreshold(val)
})

const reactModeEnabled = computed({
  get: () => prefs.reactModeEnabled.value,
  set: (val: boolean) => prefs.setReactModeEnabled(val)
})

const assistantTemperature = computed({
  get: () => prefs.assistantTemperature.value,
  set: (val: number | null) => prefs.setAssistantTemperature(val)
})

const assistantMaxTokens = computed({
  get: () => prefs.assistantMaxTokens.value,
  set: (val: number | null) => prefs.setAssistantMaxTokens(val)
})

const assistantTimeout = computed({
  get: () => prefs.assistantTimeout.value,
  set: (val: number | null) => prefs.setAssistantTimeout(val)
})
</script>

<template>
  <div class="assistant-settings-root">
    <h3 class="section-title">{{ t('assistantSettings.title') }}</h3>
    <p class="section-desc">{{ t('assistantSettings.description') }}</p>

    <el-form label-width="160px" class="assistant-form" size="small">
      <div class="group-title">{{ t('assistantSettings.paramGroup') }}</div>

      <el-form-item>
        <template #label>
          <span>
            {{ t('assistantSettings.temperature.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.temperature.help1') }}<br/>
                {{ t('assistantSettings.temperature.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-input-number
          v-model="assistantTemperature"
          :min="0.1"
          :max="2"
          :step="0.1"
          :precision="2"
          controls-position="right"
          placeholder="0.6"
        />
      </el-form-item>

      <el-form-item>
        <template #label>
          <span>
            {{ t('assistantSettings.maxTokens.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.maxTokens.help1') }}<br/>
                {{ t('assistantSettings.maxTokens.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-input-number
          v-model="assistantMaxTokens"
          :min="-1"
          :max="65536"
          :step="512"
          controls-position="right"
          placeholder="-1"
        />
      </el-form-item>

      <el-form-item>
        <template #label>
          <span>
            {{ t('assistantSettings.timeout.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.timeout.help1') }}<br/>
                {{ t('assistantSettings.timeout.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-input-number
          v-model="assistantTimeout"
          :min="10"
          :max="600"
          :step="10"
          controls-position="right"
          placeholder="90"
        />
      </el-form-item>

      <el-divider />

      <div class="group-title">{{ t('assistantSettings.modeGroup') }}</div>
      <el-form-item>
        <template #label>
          <span>
            {{ t('assistantSettings.reactMode.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.reactMode.help1') }}<br/>
                {{ t('assistantSettings.reactMode.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-switch v-model="reactModeEnabled" />
      </el-form-item>

      <el-form-item>
        <template #label>
          <span>
            {{ t('assistantSettings.contextSummary.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.contextSummary.help1') }}<br/>
                {{ t('assistantSettings.contextSummary.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-switch v-model="ctxSummaryEnabled" />
      </el-form-item>

      <el-form-item v-if="ctxSummaryEnabled">
        <template #label>
          <span>
            {{ t('assistantSettings.contextThreshold.label') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                {{ t('assistantSettings.contextThreshold.help1') }}<br/>
                {{ t('assistantSettings.contextThreshold.help2') }}
              </template>
              <el-icon class="field-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-input-number
          v-model="ctxSummaryThreshold"
          :min="1"
          :max="200"
          :step="1"
          controls-position="right"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.assistant-settings-root {
  padding: 8px 0;
}
.section-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
}
.section-desc {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}
.group-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-regular);
}
.assistant-form {
  max-width: 720px;
}
.field-help-icon {
  margin-left: 6px;
  color: var(--el-text-color-secondary);
  cursor: help;
}
</style>
