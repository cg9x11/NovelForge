
import { useWorkflowStore } from '@/stores/useWorkflowStore'
import type { WorkflowStreamCallbacks } from '@/api/workflows'

export function useWorkflowProgress() {
  const workflowStore = useWorkflowStore()

  async function startWorkflow(
    workflowId: number,
    workflowName: string,
    callbacks: WorkflowStreamCallbacks,
    resume: boolean = false,
    runId?: number
  ) {
    return await workflowStore.startWorkflowExecution(
      workflowId,
      workflowName,
      callbacks,
      resume,
      runId
    )
  }

  function pauseWorkflow(runId: number) {
    workflowStore.pauseWorkflowExecution(runId)
  }

  function getConnection(runId: number) {
    return workflowStore.getSSEConnection(runId)
  }

  return {
    startWorkflow,
    pauseWorkflow,
    getConnection
  }
}
