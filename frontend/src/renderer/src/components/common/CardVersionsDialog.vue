<template>
  <el-dialog v-model="visible" :title="t('card_versions.title')" width="80%">
    <div class="toolbar">
      <el-button size="small" @click="reload">{{ t('common.refresh') }}</el-button>
      <el-popconfirm :title="t('card_versions.confirm_clear_all')" @confirm="clearAll">
        <template #reference>
          <el-button size="small" type="danger" plain>{{ t('card_versions.clear_all') }}</el-button>
        </template>
      </el-popconfirm>
      <span class="tip">{{ t('card_versions.tip') }}</span>
    </div>

    <el-table :data="versions" style="width:100%" height="50vh" size="small" v-loading="loading">
      <el-table-column :label="t('common.time')" width="200">
        <template #default="{ row }">{{ format(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column prop="title" :label="t('common.title')" width="240" />
      <el-table-column :label="t('card_versions.content_summary')" width="320">
        <template #default="{ row }">
          <span class="summary">{{ summarize(row.content) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('card_versions.context_summary')" width="320">
        <template #default="{ row }">
          <span class="summary">{{ summarizeCtx(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="260">
        <template #default="{ row }">
          <el-button size="small" @click="preview(row)">{{ t('common.preview') }}</el-button>
          <el-popconfirm :title="t('card_versions.confirm_restore')" @confirm="restore(row)">
            <template #reference>
              <el-button size="small" type="primary">{{ t('card_versions.restore') }}</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm :title="t('card_versions.confirm_delete')" @confirm="remove(row)">
            <template #reference>
              <el-button size="small" type="danger" plain>{{ t('common.delete') }}</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="visible = false">{{ t('common.close') }}</el-button>
    </template>

    <el-drawer v-model="drawerVisible" :title="t('card_versions.preview_title')" size="70%">
      <div class="preview-wrap2">
        <div class="pane">
          <h4>{{ t('card_versions.content_compare') }}</h4>
          <div class="diff-table">
            <div class="diff-header">{{ t('card_versions.selected_version') }}</div>
            <div class="diff-header">{{ t('card_versions.current') }}</div>
            <template v-for="(row, idx) in contentDiffRows" :key="`c-${idx}`">
              <pre class="diff-cell" :class="row.left?.type ? `diff-${row.left.type}` : 'diff-empty'">{{ row.left?.text || '' }}</pre>
              <pre class="diff-cell" :class="row.right?.type ? `diff-${row.right.type}` : 'diff-empty'">{{ row.right?.text || '' }}</pre>
            </template>
          </div>
        </div>
        <div class="pane">
          <h4>{{ t('card_versions.context_compare') }}</h4>
          <div class="diff-table">
            <div class="diff-header">{{ t('card_versions.selected_version') }}</div>
            <div class="diff-header">{{ t('card_versions.current') }}</div>
            <template v-for="(row, idx) in contextDiffRows" :key="`x-${idx}`">
              <pre class="diff-cell" :class="row.left?.type ? `diff-${row.left.type}` : 'diff-empty'">{{ row.left?.text || '' }}</pre>
              <pre class="diff-cell" :class="row.right?.type ? `diff-${row.right.type}` : 'diff-empty'">{{ row.right?.text || '' }}</pre>
            </template>
          </div>
        </div>
      </div>
    </el-drawer>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { listVersions, clearVersions, deleteVersion, type CardVersionSnapshot } from '@renderer/services/versionService'
import { ElMessage } from 'element-plus'
import { cloneContextTemplates, CONTEXT_TEMPLATE_LABELS, type ContextTemplates } from '@renderer/services/contextSlots'

const { t } = useI18n()

const props = defineProps<{
  projectId: number
  cardId: number
  modelValue: boolean
  currentContent: any
  currentContextTemplates: ContextTemplates
}>()

const emit = defineEmits(['update:modelValue', 'restore'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, value => (visible.value = value))
watch(visible, value => emit('update:modelValue', value))

const versions = ref<CardVersionSnapshot[]>([])
const loading = ref(false)

function reload() {
  loading.value = true
  versions.value = listVersions(props.projectId, props.cardId)
  loading.value = false
}

watch(
  () => [props.projectId, props.cardId, props.modelValue],
  ([projectId, cardId, modelValue]) => {
    if (projectId && cardId && modelValue) reload()
  },
  { immediate: true }
)

function format(dateLike: string) {
  const date = new Date(dateLike)
  if (Number.isNaN(date.getTime())) return dateLike
  return date.toLocaleString()
}

function summarize(value: any) {
  const text = typeof value === 'string' ? value : JSON.stringify(value ?? {}, null, 2)
  return text.length > 120 ? `${text.slice(0, 120)}…` : text
}

function summarizeCtx(snapshot: CardVersionSnapshot) {
  const text = [
    `${CONTEXT_TEMPLATE_LABELS.generation}: ${String(snapshot.ai_context_template ?? '')}`,
    `${CONTEXT_TEMPLATE_LABELS.review}: ${String(snapshot.ai_context_template_review ?? '')}`,
  ].join('\n')
  return text.length > 100 ? `${text.slice(0, 100)}…` : text
}

function clearAll() {
  clearVersions(props.projectId, props.cardId)
  reload()
  ElMessage.success(t('card_versions.cleared'))
}

function remove(version: CardVersionSnapshot) {
  deleteVersion(props.projectId, props.cardId, version.id)
  reload()
  ElMessage.success(t('card_versions.deleted'))
}

const drawerVisible = ref(false)
const selectedText = ref('')
const selectedCtx = ref<ContextTemplates>(cloneContextTemplates())

const currentText = computed(() => JSON.stringify(props.currentContent ?? {}, null, 2))
const currentCtx = computed(() =>
  [
    `${CONTEXT_TEMPLATE_LABELS.generation}\n${props.currentContextTemplates?.generation ?? ''}`,
    `${CONTEXT_TEMPLATE_LABELS.review}\n${props.currentContextTemplates?.review ?? ''}`,
  ].join('\n\n')
)

function preview(version: CardVersionSnapshot) {
  selectedText.value = JSON.stringify(version.content ?? {}, null, 2)
  selectedCtx.value = cloneContextTemplates({
    generation: version.ai_context_template,
    review: version.ai_context_template_review,
  })
  drawerVisible.value = true
}

function restore(version: CardVersionSnapshot) {
  emit('restore', version)
}

interface DiffPart {
  text: string
  type: 'equal' | 'add' | 'del'
}

interface DiffRow {
  left?: DiffPart
  right?: DiffPart
}

function computeDiffRows(left: string, right: string): DiffRow[] {
  const leftLines = (left || '').split('\n')
  const rightLines = (right || '').split('\n')
  const leftCount = leftLines.length
  const rightCount = rightLines.length
  const dp: number[][] = Array.from({ length: leftCount + 1 }, () => Array(rightCount + 1).fill(0))

  for (let leftIndex = 1; leftIndex <= leftCount; leftIndex++) {
    for (let rightIndex = 1; rightIndex <= rightCount; rightIndex++) {
      dp[leftIndex][rightIndex] =
        leftLines[leftIndex - 1] === rightLines[rightIndex - 1]
          ? dp[leftIndex - 1][rightIndex - 1] + 1
          : Math.max(dp[leftIndex - 1][rightIndex], dp[leftIndex][rightIndex - 1])
    }
  }

  const rows: DiffRow[] = []
  let leftIndex = leftCount
  let rightIndex = rightCount

  while (leftIndex > 0 && rightIndex > 0) {
    if (leftLines[leftIndex - 1] === rightLines[rightIndex - 1]) {
      rows.push({
        left: { text: leftLines[leftIndex - 1], type: 'equal' },
        right: { text: rightLines[rightIndex - 1], type: 'equal' },
      })
      leftIndex--
      rightIndex--
    } else if (dp[leftIndex - 1][rightIndex] >= dp[leftIndex][rightIndex - 1]) {
      rows.push({ left: { text: leftLines[leftIndex - 1], type: 'del' } })
      leftIndex--
    } else {
      rows.push({ right: { text: rightLines[rightIndex - 1], type: 'add' } })
      rightIndex--
    }
  }

  while (leftIndex > 0) {
    rows.push({ left: { text: leftLines[leftIndex - 1], type: 'del' } })
    leftIndex--
  }
  while (rightIndex > 0) {
    rows.push({ right: { text: rightLines[rightIndex - 1], type: 'add' } })
    rightIndex--
  }

  rows.reverse()
  return rows
}

const contentDiffRows = computed<DiffRow[]>(() => computeDiffRows(selectedText.value, currentText.value))
const contextDiffRows = computed<DiffRow[]>(() =>
  computeDiffRows(
    [
      `${CONTEXT_TEMPLATE_LABELS.generation}\n${selectedCtx.value.generation}`,
      `${CONTEXT_TEMPLATE_LABELS.review}\n${selectedCtx.value.review}`,
    ].join('\n\n'),
    currentCtx.value
  )
)
</script>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.tip { color: var(--el-text-color-secondary); font-size: 12px; margin-left: auto; }
.preview-wrap2 { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: minmax(140px, auto); gap: 12px; }
.pane { overflow: auto; border: 1px solid var(--el-border-color-light); border-radius: 6px; padding: 8px; }
.summary { color: var(--el-text-color-secondary); }
.diff-table { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid var(--el-border-color-light); border-radius: 4px; overflow: hidden; }
.diff-header { background: var(--el-fill-color-light); font-weight: 600; padding: 6px 8px; border-bottom: 1px solid var(--el-border-color-light); }
.diff-cell { margin: 0; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; padding: 2px 6px; border-left: 3px solid transparent; border-bottom: 1px solid var(--el-border-color-extra-light); }
.diff-equal { background: transparent; }
.diff-add { background: rgba(46, 204, 113, 0.12); border-left-color: #2ecc71; }
.diff-del { background: rgba(231, 76, 60, 0.13); border-left-color: #e74c3c; }
.diff-empty { background: var(--el-fill-color-blank); }
</style>
