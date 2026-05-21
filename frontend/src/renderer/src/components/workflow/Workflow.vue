<template>
  <div class="workflow-container">
    <div class="workflow-toolbar">
      <div class="toolbar-left">
        <el-button @click="goBackToDashboard" plain>
          <span>{{ t('common.back') }}</span>
        </el-button>
        <el-select
          v-model="currentWorkflowId"
          :placeholder="t('workflow.select_workflow')"
          filterable
          clearable
          @change="onWorkflowChange"
          style="width: 300px"
        >
          <el-option
            v-for="wf in workflowList"
            :key="wf.id"
            :label="wf.name"
            :value="wf.id"
          >
            <span style="float: left">{{ wf.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">
              {{ formatDate(wf.updated_at) }}
            </span>
          </el-option>
        </el-select>

        <el-button @click="createNewWorkflow">
          <el-icon><Plus /></el-icon>
          <span>{{ t('common.new') }}</span>
        </el-button>

        <el-button
          @click="deleteWorkflow"
          :disabled="!currentWorkflowId"
          type="danger"
          plain
        >
          <el-icon><Delete /></el-icon>
          <span>{{ t('common.delete') }}</span>
        </el-button>
      </div>

      <div class="toolbar-right">
        <div class="toolbar-switch-item">
          <span class="switch-label">{{ t('workflow.keep_history') }}</span>
          <el-switch
            v-model="keepRunHistory"
            @change="onKeepRunHistoryChange"
            :disabled="!currentWorkflowId"
            size="small"
          />
        </div>

        <el-divider direction="vertical" />

        <el-button
          @click="showRunsDialog = true"
          plain
        >
          <el-icon><Clock /></el-icon>
          <span>{{ t('workflow.run_history') }}</span>
        </el-button>

        <el-button
          @click="validateWorkflowCode"
          :disabled="!currentWorkflowId"
          plain
        >
          <el-icon><CircleCheck /></el-icon>
          <span>{{ t('workflow.validate_code') }}</span>
        </el-button>

        <el-divider direction="vertical" />

        <el-button @click="saveWorkflow">
          <el-icon><Document /></el-icon>
          <span>{{ t('common.save') }}</span>
        </el-button>

        <el-divider direction="vertical" />

        <el-button
          v-if="canStart"
          @click="runWorkflow"
          type="primary"
        >
          <el-icon><VideoPlay /></el-icon>
          <span>{{ t('workflow.run') }}</span>
        </el-button>
        <el-button
          v-if="canPause"
          @click="pauseCurrentRun"
          type="warning"
        >
          <el-icon><VideoPause /></el-icon>
          <span>{{ t('workflow.pause') }}</span>
        </el-button>
        <el-button
          v-if="canResume"
          @click="resumeCurrentRun"
          type="success"
        >
          <el-icon><VideoPlay /></el-icon>
          <span>{{ t('workflow.resume') }}</span>
        </el-button>
      </div>
    </div>

    <div class="workflow-content">
      <div class="library-section" :style="{ width: libraryWidth + 'px' }">
        <node-library @add-node="onAddNode" />
      </div>

      <div class="resize-handle" @mousedown="startResizing('library')"></div>

      <div class="editor-section">
        <div class="section-header">
          <span class="section-title">{{ t('workflow.nodes') }}</span>
          <span class="section-subtitle" v-if="currentWorkflowName">
            {{ currentWorkflowName }}
          </span>
          <div class="view-mode-toggle" style="margin-left: auto">
             <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="visual">
                   <el-icon><List /></el-icon> {{ t('workflow.visual') }}
                </el-radio-button>
                <el-radio-button label="code">
                   <el-icon><Document /></el-icon> {{ t('workflow.code') }}
                </el-radio-button>
             </el-radio-group>
          </div>
        </div>
        <div style="flex: 1; overflow: hidden; position: relative">
            <node-block-editor
              v-if="viewMode === 'visual'"
              v-model="code"
              :is-running="isRunning"
              :workflow-id="currentWorkflowId"
              :revision="currentWorkflowRevision"
              @revision-changed="handleVisualRevisionChanged"
            />
            <code-editor
              v-else
              v-model="code"
            />
        </div>
      </div>

      <div class="resize-handle" @mousedown="startResizing('notebook')"></div>

      <div class="notebook-section" :style="{ width: notebookWidth + 'px' }">
        <workflow-notebook
          :cells="notebookCells"
          :is-running="isRunning"
          @cell-output="onCellOutput"
          @clear-output="clearOutput"
        />
      </div>
    </div>

    <workflow-runs-dialog
      v-model="showRunsDialog"
      :workflow-id="currentWorkflowId"
      @resume-run="onResumeRun"
    />

    <workflow-agent-dialog
      :workflow-id="currentWorkflowId"
      :revision="currentWorkflowRevision"
      @applied="handleWorkflowAgentApplied"
    />

    <el-dialog
      v-model="showValidationDialog"
      :title="t('workflow.validation_result')"
      width="600px"
    >
      <div v-if="validationResult">
        <el-alert
          :type="validationResult.is_valid ? 'success' : 'error'"
          :title="validationResult.is_valid ? t('workflow.validation_passed') : t('workflow.validation_failed')"
          :closable="false"
          style="margin-bottom: 16px"
        >
          <template v-if="!validationResult.is_valid">
            {{ t('workflow.found_errors', { count: validationResult.errors.length }) }}
            <span v-if="validationResult.warnings.length > 0">
              {{ t('workflow.and_warnings', { count: validationResult.warnings.length }) }}
            </span>
          </template>
        </el-alert>

        <div v-if="validationResult.errors.length > 0" style="margin-bottom: 16px">
          <h4 style="margin-bottom: 8px; color: #f56c6c">{{ t('workflow.errors') }}</h4>
          <el-scrollbar max-height="300px">
            <div
              v-for="(error, index) in validationResult.errors"
              :key="'error-' + index"
              class="validation-item error-item"
            >
              <div class="validation-header">
                <el-tag type="danger" size="small">{{ error.error_type }}</el-tag>
                <span class="validation-location">{{ t('workflow.line', { line: error.line }) }}</span>
                <span v-if="error.variable" class="validation-variable">{{ error.variable }}</span>
              </div>
              <div class="validation-message">{{ error.message }}</div>
              <div v-if="error.suggestion" class="validation-suggestion">
                💡 {{ error.suggestion }}
              </div>
            </div>
          </el-scrollbar>
        </div>

        <div v-if="validationResult.warnings.length > 0">
          <h4 style="margin-bottom: 8px; color: #e6a23c">{{ t('workflow.warnings') }}</h4>
          <el-scrollbar max-height="200px">
            <div
              v-for="(warning, index) in validationResult.warnings"
              :key="'warning-' + index"
              class="validation-item warning-item"
            >
              <div class="validation-header">
                <el-tag type="warning" size="small">{{ warning.error_type }}</el-tag>
                <span class="validation-location">{{ t('workflow.line', { line: warning.line }) }}</span>
                <span v-if="warning.variable" class="validation-variable">{{ warning.variable }}</span>
              </div>
              <div class="validation-message">{{ warning.message }}</div>
              <div v-if="warning.suggestion" class="validation-suggestion">
                💡 {{ warning.suggestion }}
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <template #footer>
        <el-button @click="showValidationDialog = false">{{ t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Document, Delete, VideoPlay, VideoPause, Close, List, Clock, CircleCheck, ArrowDown } from '@element-plus/icons-vue'
import { useAppStore } from '@renderer/stores/useAppStore'
import NodeBlockEditor from './editor/NodeBlockEditor.vue'
import CodeEditor from './editor/CodeEditor.vue'
import WorkflowNotebook from './notebook/WorkflowNotebook.vue'
import NodeLibrary from './panels/NodeLibrary.vue'
import WorkflowRunsDialog from './dialogs/WorkflowRunsDialog.vue'
import WorkflowAgentDialog from './WorkflowAgentDialog.vue'
import { useWorkflowExecution } from '@/composables/useWorkflowExecution'
import { useWorkflowProgress } from '@/composables/useWorkflowProgress'
import { applyWorkflowPatch } from '@/api/workflowAgent'
import {
  listWorkflows,
  saveCodeWorkflow,
  getCodeWorkflow,
  updateWorkflow,
  deleteWorkflow as deleteWorkflowApi,
  validateWorkflow
} from '@/api/workflows'
import request from '@/api/request'

const { t } = useI18n()
const appStore = useAppStore()

function goBackToDashboard() {
  appStore.goToDashboard()
  window.location.hash = ''
}

const {
  execution,
  isRunning,
  isPaused,
  isIdle,
  canPause,
  canResume,
  canStart,
  start: startExecution,
  updateRunId,
  pause: pauseExecution,
  resume: resumeExecution,
  complete: completeExecution,
  fail: failExecution,
  reset: resetExecution
} = useWorkflowExecution()

const { startWorkflow, pauseWorkflow } = useWorkflowProgress()

const code = ref(``)
const showRunsDialog = ref(false)
const showValidationDialog = ref(false)
const validationResult = ref(null)

const viewMode = ref('visual') // 'visual' | 'code'
const notebookCells = reactive([])
let currentWorkflowId = ref(null)
let currentWorkflowName = ref(t('workflow.untitled'))
const currentWorkflowRevision = ref('')
const keepRunHistory = ref(false)
const workflowList = ref([])

const libraryWidth = ref(280)
const notebookWidth = ref(500)
const minLibraryWidth = 200
const maxLibraryWidth = 500
const minNotebookWidth = 300
const maxNotebookWidth = 800
let resizingPanel = ref(null)
let startX = 0
let startWidth = 0

function startResizing(panel) {
  resizingPanel.value = panel
  startX = window.event.clientX
  startWidth = panel === 'library' ? libraryWidth.value : notebookWidth.value
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', handleResizing)
  window.addEventListener('mouseup', stopResizing)
}

function handleResizing(e) {
  if (!resizingPanel.value) return

  if (resizingPanel.value === 'library') {
    let newWidth = startWidth + (e.clientX - startX)
    newWidth = Math.max(minLibraryWidth, Math.min(maxLibraryWidth, newWidth))
    libraryWidth.value = newWidth
  } else if (resizingPanel.value === 'notebook') {
    let newWidth = startWidth - (e.clientX - startX)
    newWidth = Math.max(minNotebookWidth, Math.min(maxNotebookWidth, newWidth))
    notebookWidth.value = newWidth
  }
}

function stopResizing() {
  resizingPanel.value = null
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', handleResizing)
  window.removeEventListener('mouseup', stopResizing)
}

const loadWorkflowList = async () => {
  try {
    const workflows = await listWorkflows()
    workflowList.value = workflows.filter(wf => {
      return wf.dsl_version === 2
    })
  } catch (error) {
    ElMessage.error(t('workflow.messages.load_list_failed'))
  }
}

const refreshWorkflowList = async () => {
  await loadWorkflowList()
  ElMessage.success(t('workflow.messages.list_refreshed'))
}

const onWorkflowChange = async (workflowId) => {
  if (!workflowId) {
    currentWorkflowId.value = null
    currentWorkflowName.value = t('workflow.untitled')
    code.value = `# ${t('workflow.defaults.example_workflow')}
#@node(description="${t('workflow.defaults.select_project')}")
project = Logic.SelectProject(project_id=1)
#</node>

#@node(description="${t('workflow.defaults.load_novel_catalog')}")
novel = Novel.Load(root_path="E:\\\\Novels\\\\book")
#</node>

#@node(description="${t('workflow.defaults.batch_create_volume_cards')}")
cards = Card.BatchUpsert(
    items=novel.volume_list,
    card_type="volume",
    title_template="{item}"
)
#</node>`
    notebookCells.length = 0
    return
  }

  try {
    const workflow = await getCodeWorkflow(workflowId)
    currentWorkflowId.value = workflow.id
    currentWorkflowName.value = workflow.name
    code.value = workflow.code || ''
    currentWorkflowRevision.value = workflow.revision || ''
    keepRunHistory.value = workflow.keep_run_history || false
    notebookCells.length = 0
  } catch (error) {
    ElMessage.error(t('workflow.messages.load_workflow_failed'))
  }
}

const createNewWorkflow = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt(t('workflow.dialogs.new_name_prompt'), t('workflow.dialogs.new_title'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputValue: t('workflow.defaults.new_workflow'),
      inputPattern: /\S+/,
      inputErrorMessage: t('workflow.validation.name_required'),
      inputValidator: (value) => {
        if (!value || !value.trim()) {
          return t('workflow.validation.name_required')
        }
        const exists = workflowList.value.some(wf => wf.name === value.trim())
        if (exists) {
          return t('workflow.validation.name_exists')
        }
        return true
      }
    })

    const initialCode = `# ${t('workflow.defaults.new_workflow_comment')}
#@node(description="${t('workflow.defaults.select_project')}")
project = Logic.SelectProject(project_id=1)
#</node>`
    const workflow = await saveCodeWorkflow(name, initialCode)
    currentWorkflowId.value = workflow.id
    currentWorkflowName.value = workflow.name
    code.value = initialCode
    currentWorkflowRevision.value = ''

    await loadWorkflowList()

    ElMessage.success(t('workflow.messages.created', { name: workflow.name }))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('workflow.messages.create_failed'))
    }
  }
}

const deleteWorkflow = async () => {
  if (!currentWorkflowId.value) {
    ElMessage.warning(t('workflow.messages.select_before_delete'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('workflow.messages.confirm_delete', { name: currentWorkflowName.value }),
      t('workflow.dialogs.delete_title'),
      {
        confirmButtonText: t('workflow.actions.confirm_delete'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )

    await deleteWorkflowApi(currentWorkflowId.value)

    currentWorkflowId.value = null
    currentWorkflowName.value = t('workflow.untitled')
    currentWorkflowRevision.value = ''
    code.value = `# ${t('workflow.defaults.example_workflow')}
#@node(description="${t('workflow.defaults.select_project')}")
project = Logic.SelectProject(project_id=1)
#</node>

#@node(description="${t('workflow.defaults.load_novel_catalog')}")
novel = Novel.Load(root_path="E:\\\\Novels\\\\book")
#</node>

#@node(description="${t('workflow.defaults.batch_create_volume_cards')}")
cards = Card.BatchUpsert(
    items=novel.volume_list,
    card_type="volume",
    title_template="{item}"
)
#</node>`
    notebookCells.length = 0

    await loadWorkflowList()

    ElMessage.success(t('workflow.messages.deleted'))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('workflow.messages.delete_failed'))
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return t('workflow.time.just_now')
  if (diff < 3600000) return t('workflow.time.minutes_ago', { count: Math.floor(diff / 60000) })
  if (diff < 86400000) return t('workflow.time.hours_ago', { count: Math.floor(diff / 3600000) })
  if (diff < 604800000) return t('workflow.time.days_ago', { count: Math.floor(diff / 86400000) })

  return date.toLocaleDateString('zh-CN')
}

const onKeepRunHistoryChange = async (value) => {
  if (!currentWorkflowId.value) return

  try {
    await updateWorkflow(currentWorkflowId.value, {
      keep_run_history: value
    })
    ElMessage.success(value ? t('workflow.messages.history_persistence_enabled') : t('workflow.messages.history_persistence_disabled'))
  } catch (error) {
    ElMessage.error(t('workflow.messages.update_persistence_failed'))
    keepRunHistory.value = !value
  }
}

const runWorkflow = async () => {
  if (!canStart.value) return

  notebookCells.length = 0

  try {
    if (currentWorkflowId.value) {
      await updateWorkflow(currentWorkflowId.value, {
        definition_code: code.value
      })
      currentWorkflowRevision.value = ''
    } else {
      const workflow = await saveCodeWorkflow(currentWorkflowName.value, code.value)
      currentWorkflowId.value = workflow.id
    }

    await startWorkflow(
      currentWorkflowId.value,
      currentWorkflowName.value,
      {
        onRunStarted: (actualRunId) => {
          updateRunId(actualRunId)
        },
        onStart: (event) => {
          notebookCells.push({
            id: event.statement?.variable || 'unknown',
            type: 'execution',
            content: event.statement?.code || '',
            description: event.statement?.description || '',
            status: 'running',
            outputs: []
          })
        },
        onProgress: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            const updatedCell = {
              ...notebookCells[cellIndex],
              status: 'progress',
              progress: event.percent,
              message: event.message
            }
            notebookCells.splice(cellIndex, 1, updatedCell)
          }
        },
        onComplete: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            notebookCells[cellIndex] = {
              ...notebookCells[cellIndex],
              status: 'completed',
              outputs: [event.result],
              resumed: event.resumed || false
            }
          } else {
            notebookCells.push({
              id: event.statement?.variable || 'unknown',
              type: 'execution',
              content: event.statement?.code || '',
              status: 'completed',
              outputs: [event.result],
              resumed: true
            })
          }
        },
        onError: (event) => {
          const cell = notebookCells.find(c => c.id === event.statement?.variable)
          if (cell) {
            cell.status = 'error'
            cell.error = event.error
          } else {
            notebookCells.push({
              id: 'error-' + Date.now(),
              type: 'execution',
              content: event.statement?.code || t('workflow.messages.code_parse_failed'),
              status: 'error',
              error: event.error || t('common.unknown_error'),
              outputs: []
            })
          }
          failExecution(event.error || t('workflow.messages.execution_failed'))
          ElMessage.error(event.error || t('workflow.messages.execution_failed'))
        },
        onEnd: () => {
          if (execution.state === 'running') {
            completeExecution()
          }
        }
      },
      false
    )

    startExecution(currentWorkflowId.value, 0)
  } catch (error) {
    failExecution(error.message || t('workflow.messages.execution_failed'))
    ElMessage.error(error.message || t('workflow.messages.execution_failed'))
  }
}

const clearOutput = () => {
  notebookCells.length = 0
  if (!isIdle.value) {
    resetExecution()
  }
}

const pauseCurrentRun = async () => {
  if (!canPause.value) return

  if (execution.runId === null || execution.runId === undefined) {
    return
  }

  try {

    pauseWorkflow(execution.runId)

    await request.post(`/workflows/runs/${execution.runId}/pause`, {}, '/api')

    pauseExecution()

    ElMessage.success(t('workflow.messages.paused'))
  } catch (error) {
    ElMessage.error(t('workflow.messages.pause_failed', { error: error.message || error }))
  }
}

const resumeCurrentRun = async () => {
  if (!canResume.value) return

  if (execution.runId === null || execution.runId === undefined || execution.workflowId === null || execution.workflowId === undefined) {
    return
  }

  try {
    notebookCells.length = 0

    await startWorkflow(
      execution.workflowId,
      currentWorkflowName.value,
      {
        onStart: (event) => {
          notebookCells.push({
            id: event.statement?.variable || 'unknown',
            type: 'execution',
            content: event.statement?.code || '',
            status: 'running',
            outputs: []
          })
        },
        onProgress: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            const updatedCell = {
              ...notebookCells[cellIndex],
              status: 'progress',
              progress: event.percent,
              message: event.message
            }
            notebookCells.splice(cellIndex, 1, updatedCell)
          }
        },
        onComplete: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            notebookCells[cellIndex] = {
              ...notebookCells[cellIndex],
              status: 'completed',
              outputs: [event.result],
              resumed: event.resumed || false
            }
          } else {
            notebookCells.push({
              id: event.statement?.variable || 'unknown',
              type: 'execution',
              content: event.statement?.code || '',
              description: event.statement?.description || '',
              status: 'completed',
              outputs: [event.result],
              resumed: true
            })
          }
        },
        onError: (event) => {
          const cell = notebookCells.find(c => c.id === event.statement?.variable)
          if (cell) {
            cell.status = 'error'
            cell.error = event.error
          } else {
            notebookCells.push({
              id: 'error-' + Date.now(),
              type: 'execution',
              content: event.statement?.code || t('workflow.messages.code_parse_failed'),
              description: event.statement?.description || '',
              status: 'error',
              error: event.error || t('common.unknown_error'),
              outputs: []
            })
          }
          failExecution(event.error || t('workflow.messages.execution_failed'))
          ElMessage.error(event.error || t('workflow.messages.execution_failed'))
        },
        onEnd: () => {
          if (execution.state === 'running') {
            completeExecution()
          }
        }
      },
      true, // resume=true
      execution.runId
    )

    resumeExecution()

    ElMessage.success(t('workflow.messages.resumed'))
  } catch (error) {
    failExecution(error.message || t('workflow.messages.resume_failed'))
    ElMessage.error(error.message || t('workflow.messages.resume_failed'))
  }
}

const cancelCurrentRun = async () => {
  if (!currentRunId.value) return

  try {
    await ElMessageBox.confirm(t('workflow.messages.cancel_confirm'), t('workflow.messages.confirm_cancel'), {
      type: 'warning'
    })

    await request.post(`/workflows/runs/${currentRunId.value}/cancel`, {}, '/api')
    ElMessage.success(t('workflow.messages.workflow_cancelled'))

    isRunning.value = false
    isPaused.value = false
    currentRunId.value = null
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('workflow.messages.cancel_failed', { reason: error.message || error }))
    }
  }
}

const saveWorkflow = async () => {
  try {
    if (currentWorkflowId.value) {
      await updateWorkflow(currentWorkflowId.value, {
        definition_code: code.value
      })
      try {
        const workflowData = await getCodeWorkflow(currentWorkflowId.value)
        currentWorkflowRevision.value = workflowData.revision || ''
      } catch {
        // ignore
      }
      ElMessage.success(t('workflow.messages.workflow_updated'))
    } else {
      const { value: name } = await ElMessageBox.prompt(t('workflow.messages.enter_workflow_name'), t('workflow.messages.save_workflow'), {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        inputValue: currentWorkflowName.value,
        inputPattern: /\S+/,
        inputErrorMessage: t('workflow.messages.workflow_name_required')
      })

      const workflow = await saveCodeWorkflow(name, code.value)
      currentWorkflowId.value = workflow.id
      currentWorkflowName.value = workflow.name
      currentWorkflowRevision.value = ''
      ElMessage.success(t('workflow.messages.workflow_saved', { name: workflow.name }))
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || t('workflow.messages.save_failed'))
    }
  }
}

const validateWorkflowCode = async () => {
  if (!currentWorkflowId.value) {
    ElMessage.warning(t('workflow.messages.select_or_save_first'))
    return
  }

  try {
    const runPatchDryRun = async () => {
      return applyWorkflowPatch(currentWorkflowId.value, {
        base_revision: currentWorkflowRevision.value || '',
        patch_ops: [
          {
            op: 'replace_code',
            new_code: code.value || '',
            reason: 'ui_validate',
          },
        ],
        dry_run: true,
      })
    }

    let patchResult
    try {
      patchResult = await runPatchDryRun()
    } catch (error) {
      const status = error?.response?.status
      const detail = error?.response?.data?.detail
      if (status === 409 && detail?.code === 'revision_mismatch') {
        const workflowData = await getCodeWorkflow(currentWorkflowId.value)
        currentWorkflowRevision.value = workflowData.revision || currentWorkflowRevision.value
        patchResult = await runPatchDryRun()
      } else {
        throw error
      }
    }

    validationResult.value = patchResult?.validation || {
      is_valid: false,
      errors: [
        {
          line: 0,
          variable: '',
          error_type: 'unknown',
          message: patchResult?.error || t('workflow.messages.validation_failed'),
          suggestion: null,
        },
      ],
      warnings: [],
    }
    showValidationDialog.value = true

    if (validationResult.value.is_valid) {
      ElMessage.success(t('workflow.validation_passed'))
    } else {
      ElMessage.error(t('workflow.found_errors', { count: validationResult.value.errors.length }))
    }
  } catch (error) {
    ElMessage.error(t('workflow.messages.validation_failed'))
  }
}

const onCodeChange = (newCode) => {
  code.value = newCode
}

// const onNodeSelected = (node) => {
//   selectedNode.value = node
// }

const onNodeUpdate = (updatedNode) => {
  const lines = code.value.split('\n')

  let updated = false
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes(`${updatedNode.variable} =`)) {
      lines[i] = updatedNode.code
      updated = true
      break
    }
  }

  if (updated) {
    code.value = lines.join('\n')
    ElMessage.success(t('workflow.messages.node_updated'))
  } else {
      ElMessage.error(t('workflow.messages.node_not_found'))
  }
}

const onAddNode = (nodeType) => {
  const baseName = generateVariableName(nodeType)
  const variableName = generateUniqueVariableName(baseName)

  const nodeCode = `#@node()
${variableName} = ${nodeType}()
#</node>`

  const newCode = code.value.trim()
  if (newCode) {
    code.value = newCode + '\n\n' + nodeCode
  } else {
    code.value = nodeCode
  }

  ElMessage.success(t('workflow.messages.node_added'))
}

const PYTHON_RESERVED_WORDS = new Set([
  'false', 'none', 'true', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
  'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
  'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
  'raise', 'return', 'try', 'while', 'with', 'yield'
])

function normalizePythonVariableName(value) {
  const normalized = String(value || 'node')
    .replace(/[^a-zA-Z0-9_]/g, '_')
    .replace(/^([0-9])/, '_$1')
    .toLowerCase()
  const safeName = normalized || 'node'
  return PYTHON_RESERVED_WORDS.has(safeName) ? `${safeName}_node` : safeName
}

function generateVariableName(nodeType) {
  const parts = nodeType.split('.')
  if (parts.length >= 2) {
    const method = parts[1].toLowerCase()
      const cleanMethod = method.replace(/^(get|set|create|update|delete|fetch|load)_?/, '')
    return normalizePythonVariableName(cleanMethod || method)
  }
  return normalizePythonVariableName(nodeType.replace(/\./g, '_'))
}

function generateUniqueVariableName(baseName) {
  let counter = 2
  let variableName = baseName

  const allLines = code.value.split('\n')
  const usedVariables = new Set()

  allLines.forEach(line => {
    const assignMatch = line.match(/^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*/)
    if (assignMatch) {
      usedVariables.add(assignMatch[1])
    }
  })

  while (usedVariables.has(variableName)) {
    variableName = `${baseName}${counter++}`
  }

  return variableName
}

const onCellOutput = (output) => {
}

const onResumeRun = async (run) => {
  notebookCells.length = 0

  let workflowData
  try {
    workflowData = await getCodeWorkflow(run.workflow_id)
    code.value = workflowData.code || ''
    currentWorkflowName.value = workflowData.name
    currentWorkflowId.value = run.workflow_id
    currentWorkflowRevision.value = workflowData.revision || ''
  } catch (error) {
    ElMessage.error(t('workflow.messages.load_workflow_failed'))
    return
  }

  try {
    await startWorkflow(
      run.workflow_id,
      workflowData.name,
      {
        onStart: (event) => {
          notebookCells.push({
            id: event.statement?.variable || 'unknown',
            type: 'execution',
            content: event.statement?.code || '',
            description: event.statement?.description || '',
            status: 'running',
            outputs: []
          })
        },
        onProgress: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            const updatedCell = {
              ...notebookCells[cellIndex],
              status: 'progress',
              progress: event.percent,
              message: event.message
            }
            notebookCells.splice(cellIndex, 1, updatedCell)
          }
        },
        onComplete: (event) => {
          const cellIndex = notebookCells.findIndex(c => c.id === event.statement?.variable)
          if (cellIndex !== -1) {
            notebookCells[cellIndex] = {
              ...notebookCells[cellIndex],
              status: 'completed',
              outputs: [event.result],
              resumed: event.resumed || false
            }
          } else {
            notebookCells.push({
              id: event.statement?.variable || 'unknown',
              type: 'execution',
              content: event.statement?.code || '',
              description: event.statement?.description || '',
              status: 'completed',
              outputs: [event.result],
              resumed: true
            })
          }
        },
        onError: (event) => {
          const cell = notebookCells.find(c => c.id === event.statement?.variable)
          if (cell) {
            cell.status = 'error'
            cell.error = event.error
          } else {
            notebookCells.push({
              id: 'error-' + Date.now(),
              type: 'execution',
              content: event.statement?.code || t('workflow.messages.code_parse_failed'),
              description: event.statement?.description || '',
              status: 'error',
              error: event.error || t('common.unknown_error'),
              outputs: []
            })
          }
          failExecution(event.error || t('workflow.messages.execution_failed'))
          ElMessage.error(event.error || t('workflow.messages.execution_failed'))
        },
        onEnd: () => {
          if (execution.state === 'running') {
            completeExecution()
          }
        }
      },
      true, // resume=true
      run.id
    )

    startExecution(run.workflow_id, run.id)
  } catch (error) {
    failExecution(error.message || t('workflow.messages.resume_failed'))
    ElMessage.error(error.message || t('workflow.messages.resume_failed'))
  }
}

onUnmounted(() => {
})

onMounted(() => {
  loadWorkflowList()
})

const handleWorkflowAgentApplied = (payload) => {
  code.value = payload.newCode || code.value
  if (payload.newRevision) {
    currentWorkflowRevision.value = payload.newRevision
  }
}

const handleVisualRevisionChanged = (revision) => {
  if (typeof revision === 'string' && revision.trim()) {
    currentWorkflowRevision.value = revision
  }
}
</script>

<style scoped>
.workflow-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color-page);
}

.workflow-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  box-shadow: 0 1px 4px var(--el-box-shadow-light);
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-switch-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  height: 32px;
  border-radius: 4px;
  background: var(--el-fill-color-light);
}

.switch-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.dropdown-switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  min-width: 180px;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.workflow-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 0;
  background: var(--el-border-color-lighter);
  position: relative;
}

.library-section {
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  overflow: hidden;
  flex-shrink: 0;
}

.resize-handle {
  width: 4px;
  background: var(--el-border-color-lighter);
  cursor: col-resize;
  flex-shrink: 0;
  position: relative;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background: var(--el-color-primary);
}

.resize-handle:active {
  background: var(--el-color-primary);
}

.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  overflow: hidden;
  min-width: 400px;
}

.property-section {
  width: 350px;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  overflow: hidden;
}

.notebook-section {
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  overflow: hidden;
  flex-shrink: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.section-subtitle {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.validation-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border-left: 3px solid;
}

.error-item {
  background-color: var(--el-color-danger-light-9);
  border-left-color: var(--el-color-danger);
}

.warning-item {
  background-color: var(--el-color-warning-light-9);
  border-left-color: var(--el-color-warning);
}

.validation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.validation-location {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.validation-variable {
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: var(--el-text-color-regular);
  background-color: var(--el-fill-color);
  padding: 2px 6px;
  border-radius: 3px;
}

.validation-message {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.validation-suggestion {
  font-size: 13px;
  color: var(--el-text-color-regular);
  font-style: italic;
}
</style>
