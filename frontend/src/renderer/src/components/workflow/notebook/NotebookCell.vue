<template>
  <div class="notebook-cell" :class="cellStatusClass">
    <div class="cell-header">
      <div class="cell-info">
        <span class="cell-variable">{{ cell.id }}</span>
        <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
      </div>
      <div class="cell-progress" v-if="cell.status === 'progress'">
        <el-progress :percentage="cell.progress || 0" :format="() => cell.message || t('notebook_cell.processing')" :stroke-width="6" />
      </div>
    </div>

    <div class="cell-content">
      <div class="cell-code">
        <pre><code>{{ cell.content }}</code></pre>
      </div>

      <div v-if="cell.description" class="cell-description">
        {{ cell.description }}
      </div>

      <div class="cell-output" v-if="hasOutput">
        <div v-if="cell.status === 'completed'" class="output-success">
          <div class="output-header">
            <el-icon><SuccessFilled /></el-icon>
            <span>{{ t('notebook_cell.success') }}</span>
          </div>
          <div class="output-content">
            <pre>{{ formatOutput(cell.outputs) }}</pre>
          </div>
        </div>

        <div v-if="cell.status === 'error'" class="output-error">
          <div class="output-header">
            <el-icon><CircleCloseFilled /></el-icon>
            <span>{{ t('notebook_cell.failed') }}</span>
          </div>
          <div class="output-content">
            <pre>{{ cell.error }}</pre>
          </div>
        </div>

        <div v-if="cell.status === 'progress'" class="output-progress">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ cell.message || t('notebook_cell.processing') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { SuccessFilled, CircleCloseFilled, Loading } from '@element-plus/icons-vue'

const props = defineProps({ cell: { type: Object, required: true } })
defineEmits(['output'])
const { t } = useI18n()

const cellStatusClass = computed(() => `cell-status-${props.cell.status}`)
const statusTagType = computed(() => ({ running: 'info', progress: 'warning', completed: 'success', error: 'danger' }[props.cell.status] || 'info'))
const statusText = computed(() => ({ running: t('notebook_cell.status.running'), progress: t('notebook_cell.status.progress'), completed: t('notebook_cell.status.completed'), error: t('notebook_cell.status.error') }[props.cell.status] || t('notebook_cell.status.unknown')))
const hasOutput = computed(() => props.cell.status === 'completed' || props.cell.status === 'error' || props.cell.status === 'progress')
const formatOutput = (outputs) => {
  if (!outputs || outputs.length === 0) return ''
  const output = outputs[0]
  if (typeof output === 'object') return JSON.stringify(output, null, 2)
  return String(output)
}
</script>

<style scoped>
.notebook-cell {
  margin-bottom: 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  background: var(--el-bg-color);
  transition: all 0.3s;
}
.notebook-cell:hover { box-shadow: 0 2px 8px var(--el-box-shadow-light); }
</style>
