
import { reactive, readonly, computed } from 'vue'
import { i18n } from '@renderer/i18n'

export enum WorkflowState {
  IDLE = 'idle',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface WorkflowExecution {
  state: WorkflowState
  runId: number | null
  workflowId: number | null
  error: string | null
}

export function useWorkflowExecution() {
  const execution = reactive<WorkflowExecution>({
    state: WorkflowState.IDLE,
    runId: null,
    workflowId: null,
    error: null
  })

  const validTransitions: Record<WorkflowState, WorkflowState[]> = {
    [WorkflowState.IDLE]: [WorkflowState.RUNNING],
    [WorkflowState.RUNNING]: [WorkflowState.PAUSED, WorkflowState.COMPLETED, WorkflowState.FAILED],
    [WorkflowState.PAUSED]: [WorkflowState.RUNNING, WorkflowState.FAILED],
    [WorkflowState.COMPLETED]: [WorkflowState.IDLE, WorkflowState.RUNNING],
    [WorkflowState.FAILED]: [WorkflowState.IDLE, WorkflowState.RUNNING]
  }

  const isRunning = computed(() => execution.state === WorkflowState.RUNNING)
  const isPaused = computed(() => execution.state === WorkflowState.PAUSED)
  const isIdle = computed(() => execution.state === WorkflowState.IDLE)
  const isCompleted = computed(() => execution.state === WorkflowState.COMPLETED)
  const isFailed = computed(() => execution.state === WorkflowState.FAILED)
  const canPause = computed(() => execution.state === WorkflowState.RUNNING)
  const canResume = computed(() => execution.state === WorkflowState.PAUSED)
  const canStart = computed(() =>
    execution.state === WorkflowState.IDLE ||
    execution.state === WorkflowState.COMPLETED ||
    execution.state === WorkflowState.FAILED
  )

  function transitionTo(newState: WorkflowState) {
    const currentState = execution.state
    const allowedStates = validTransitions[currentState]

    if (!allowedStates.includes(newState)) {
      throw new Error(i18n.global.t('workflow_execution.invalid_transition', {
        from: currentState,
        to: newState,
        allowed: allowedStates.join(', ')
      }))
    }

    execution.state = newState
  }

  function start(workflowId: number, runId: number) {
    if (execution.state === WorkflowState.COMPLETED || execution.state === WorkflowState.FAILED) {
    }

    transitionTo(WorkflowState.RUNNING)
    execution.workflowId = workflowId
    execution.runId = runId
    execution.error = null
  }

  function updateRunId(runId: number) {
    execution.runId = runId
  }

  function pause() {
    transitionTo(WorkflowState.PAUSED)
  }

  function resume() {
    transitionTo(WorkflowState.RUNNING)
  }

  function complete() {
    transitionTo(WorkflowState.COMPLETED)
  }

  function fail(error: string) {
    transitionTo(WorkflowState.FAILED)
    execution.error = error
  }

  function reset() {
    transitionTo(WorkflowState.IDLE)
    execution.runId = null
    execution.workflowId = null
    execution.error = null
  }

  return {
    execution: readonly(execution),

    isRunning,
    isPaused,
    isIdle,
    isCompleted,
    isFailed,
    canPause,
    canResume,
    canStart,

    start,
    updateRunId,
    pause,
    resume,
    complete,
    fail,
    reset
  }
}
