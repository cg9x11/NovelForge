<template>
  <el-dialog
    v-model="visible"
    :title="t('workflow.runs.title')"
    width="90%"
    :close-on-click-modal="false"
  >
    <div class="runs-dialog-content">
      <!-- 过滤器 -->
      <div class="filters">
        <el-select v-model="statusFilter" :placeholder="t('workflow.runs.status_filter')" clearable @change="loadRuns" style="width: 150px">
          <el-option :label="t('workflow.runs.all')" value="" />
          <el-option :label="t('workflow.status.running')" value="running" />
          <el-option :label="t('workflow.status.paused')" value="paused" />
          <el-option :label="t('workflow.status.succeeded')" value="succeeded" />
          <el-option :label="t('workflow.status.failed')" value="failed" />
        </el-select>
        <el-button @click="loadRuns" :icon="Refresh">{{ t('common.refresh') }}</el-button>
      </div>

      <!-- 运行列表 -->
      <el-table :data="runs" v-loading="loading" stripe style="margin-top: 10px">
        <el-table-column prop="id" :label="t('workflow.runs.id')" width="60" />
        
        <el-table-column :label="t('workflow.runs.workflow')" width="180">
          <template #default="{ row }">
            {{ row.workflow?.name || t('workflow.runs.workflow_fallback', { id: row.workflow_id }) }}
          </template>
        </el-table-column>

        <el-table-column :label="t('workflow.runs.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="t('workflow.runs.progress')" width="150">
          <template #default="{ row }">
            <el-progress 
              v-if="row.status === 'running' || row.status === 'paused'"
              :percentage="getProgress(row.id)" 
              :status="row.status === 'paused' ? 'warning' : undefined"
              :stroke-width="8"
            />
            <el-progress 
              v-else-if="row.status === 'succeeded'"
              :percentage="100" 
              status="success"
              :stroke-width="8"
            />
            <el-progress 
              v-else-if="row.status === 'failed'"
              :percentage="100" 
              status="exception"
              :stroke-width="8"
            />
          </template>
        </el-table-column>

        <el-table-column :label="t('workflow.runs.created_at')" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column :label="t('workflow.runs.actions')" fixed="right" width="320">
          <template #default="{ row }">
            <div style="display: flex; gap: 4px; flex-wrap: nowrap;">
              <el-button
                v-if="row.status === 'running'"
                @click="pauseRun(row.id)"
                :icon="VideoPause"
                size="small"
              >
                {{ t('workflow.pause') }}
              </el-button>

              <el-button
                v-if="row.status === 'paused' || row.status === 'failed'"
                type="primary"
                @click="resumeRunFromDialog(row)"
                :icon="VideoPlay"
                size="small"
              >
                {{ t('workflow.resume') }}
              </el-button>

              <el-button
                @click="viewNodeStatus(row.id)"
                :icon="List"
                size="small"
              >
                {{ t('workflow.runs.status') }}
              </el-button>
              
              <el-button
                type="danger"
                @click="deleteRun(row.id)"
                :icon="Delete"
                plain
                size="small"
              >
                {{ t('common.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 节点状态对话框 -->
    <el-dialog
      v-model="nodeStatusVisible"
      :title="t('workflow.runs.node_execution_status')"
      width="700px"
      append-to-body
    >
      <el-table :data="nodeStatuses" v-loading="loadingNodeStatus" size="small">
        <el-table-column prop="node_id" :label="t('workflow.runs.node_id')" width="120" />
        <el-table-column prop="node_type" :label="t('workflow.runs.node_type')" width="150" />
        <el-table-column :label="t('workflow.runs.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('workflow.runs.progress')" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column prop="error" :label="t('workflow.errors')" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, VideoPause, VideoPlay, Close, List, Delete } from '@element-plus/icons-vue'
import { deleteRun as deleteRunApi } from '@renderer/api/workflows'
import request from '@renderer/api/request'

const { t } = useI18n()

interface WorkflowRun {
  id: number
  workflow_id: number
  status: string
  created_at: string
  workflow?: {
    id: number
    name: string
  }
}

interface NodeStatus {
  node_id: string
  node_type: string
  status: string
  progress: number
  error?: string
}

interface RunStatusResponse {
  nodes: NodeStatus[]
}

const props = defineProps<{
  modelValue: boolean
  workflowId?: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'resume-run', run: WorkflowRun): void
}>()

const visible = ref(props.modelValue)
const runs = ref<WorkflowRun[]>([])
const loading = ref(false)
const statusFilter = ref('')
const progressCache = ref<Record<number, number>>({})

const nodeStatusVisible = ref(false)
const nodeStatuses = ref<NodeStatus[]>([])
const loadingNodeStatus = ref(false)

let refreshTimer: number | null = null

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadRuns()
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    stopAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = window.setInterval(() => {
    if (runs.value.some(r => r.status === 'running' || r.status === 'paused')) {
      loadRuns(true)
    }
  }, 3000)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

async function loadRuns(silent = false) {
  if (!silent) {
    loading.value = true
  }

  try {
    const params: any = { limit: 50, offset: 0 }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    // 如果指定了 workflowId，只加载该工作流的运行记录
    const url = props.workflowId 
      ? `/workflows/${props.workflowId}/runs`
      : '/runs'
    
    const response = await request.get<WorkflowRun[]>(url, params, '/api')
    runs.value = response

    // 加载运行中任务的进度
    for (const run of runs.value) {
      if (run.status === 'running' || run.status === 'paused') {
        loadProgress(run.id)
      }
    }
  } catch (error: any) {
    if (!silent) {
      ElMessage.error(t('workflow_runs.messages.load_runs_failed', { error: error.message || error }))
    }
  } finally {
    if (!silent) {
      loading.value = false
    }
  }
}

async function loadProgress(runId: number) {
  try {
    const status = await request.get<RunStatusResponse>(
      `/workflows/runs/${runId}/status`,
      {},
      '/api',
      { showLoading: false }
    )
    
    if (status.nodes && status.nodes.length > 0) {
      const totalProgress = status.nodes.reduce((sum: number, node: NodeStatus) => {
        return sum + node.progress
      }, 0)
      progressCache.value[runId] = Math.round(totalProgress / status.nodes.length)
    }
  } catch (error) {
    // 静默失败，避免干扰用户
    console.warn(`[WorkflowRunsDialog] 加载进度失败: runId=${runId}`, error)
  }
}

function getProgress(runId: number): number {
  return progressCache.value[runId] || 0
}

async function pauseRun(runId: number) {
  try {
    await request.post(`/workflows/runs/${runId}/pause`, {}, '/api')
    ElMessage.success(t('workflow_runs.messages.paused'))
    loadRuns()
  } catch (error: any) {
    ElMessage.error(t('workflow_runs.messages.pause_failed', { error: error.message || error }))
  }
}

async function resumeRun(runId: number) {
  try {
    await request.post(`/workflows/runs/${runId}/resume`, {}, '/api')
    ElMessage.success(t('workflow_runs.messages.resumed_from_checkpoint'))
    loadRuns()
  } catch (error: any) {
    ElMessage.error(t('workflow_runs.messages.resume_failed', { error: error.message || error }))
  }
}

async function resumeRunFromDialog(run: WorkflowRun) {
  try {
    // 关闭对话框
    visible.value = false
    
    // 通知父组件恢复执行
    emit('resume-run', run)
    
    ElMessage.success(t('workflow_runs.messages.resuming'))
  } catch (error: any) {
    ElMessage.error(t('workflow_runs.messages.resume_failed', { error: error.message || error }))
  }
}

async function cancelRun(runId: number) {
  try {
    await ElMessageBox.confirm(t('workflow_runs.messages.confirm_cancel_run'), t('workflow_runs.dialogs.confirm_cancel'), {
      type: 'warning'
    })

    await request.post(`/workflows/runs/${runId}/cancel`, {}, '/api')
    ElMessage.success(t('workflow_runs.messages.cancelled'))
    loadRuns()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('workflow_runs.messages.cancel_failed', { error: error.message || error }))
    }
  }
}

async function viewNodeStatus(runId: number) {
  nodeStatusVisible.value = true
  loadingNodeStatus.value = true

  try {
    const status = await request.get<RunStatusResponse>(`/workflows/runs/${runId}/status`, {}, '/api')
    nodeStatuses.value = status.nodes || []
  } catch (error: any) {
    ElMessage.error(t('workflow_runs.messages.load_node_status_failed', { error: error.message || error }))
  } finally {
    loadingNodeStatus.value = false
  }
}

async function deleteRun(runId: number) {
  try {
    await ElMessageBox.confirm(t('workflow_runs.messages.confirm_delete_run'), t('workflow_runs.dialogs.confirm_delete'), {
      type: 'warning',
      confirmButtonText: t('workflow_runs.actions.confirm_delete'),
      cancelButtonText: t('common.cancel')
    })

    await deleteRunApi(runId)
    ElMessage.success(t('workflow_runs.messages.run_deleted'))
    loadRuns()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('workflow_runs.messages.delete_failed', { error: error.message || error }))
    }
  }
}

function getStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    running: 'primary',
    paused: 'warning',
    succeeded: 'success',
    failed: 'danger',
    cancelled: 'info',
    idle: 'info',
    pending: 'info',
    success: 'success',
    error: 'danger'
  }
  return typeMap[status] || 'info'
}

function getStatusLabel(status: string): string {
  const labelMap: Record<string, string> = {
    running: t('workflow_runs.status.running'),
    paused: t('workflow_runs.status.paused'),
    succeeded: t('workflow_runs.status.succeeded'),
    failed: t('workflow_runs.status.failed'),
    cancelled: t('workflow_runs.status.cancelled'),
    idle: t('workflow_runs.status.idle'),
    pending: t('workflow_runs.status.pending'),
    success: t('workflow_runs.status.success'),
    error: t('workflow_runs.status.error'),
    skipped: t('workflow_runs.status.skipped')
  }
  return labelMap[status] || status
}

function formatTime(time?: string | number): string {
  if (!time) return '-'
  
  // 如果是数字（Unix 时间戳），需要乘以 1000 转换为毫秒
  // 但如果数字很小（< 100000000），说明可能是错误的数据
  if (typeof time === 'number') {
    console.warn('[formatTime] 收到数字类型的时间戳:', time)
    if (time < 100000000) {
      console.error('[formatTime] 时间戳异常小，可能是错误数据')
      return t('workflow_runs.time.invalid_data')
    }
    time = time * 1000 // 转换为毫秒
  }
  
  const date = new Date(time)
  
  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    console.error('[formatTime] 无效的日期:', time)
    return t('workflow_runs.time.invalid_date')
  }
  
  // 检查日期是否在合理范围内（2020-2030）
  const year = date.getFullYear()
  if (year < 2020 || year > 2030) {
    console.error('[formatTime] 日期超出合理范围:', date.toISOString(), '原始值:', time)
    return t('workflow_runs.time.abnormal_date')
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.runs-dialog-content {
  min-height: 400px;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}
</style>
