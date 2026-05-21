import request, { API_BASE_URL } from './request'
import type { components } from '@/types/generated'

// ============================================================
// ============================================================
// ============================================================

export type WorkflowRead = components['schemas']['WorkflowRead']
export type WorkflowUpdate = components['schemas']['WorkflowUpdate']
export type WorkflowRunRead = components['schemas']['WorkflowRunRead']
export type NodeExecutionStatus = components['schemas']['NodeExecutionStatus']

export function listWorkflows(): Promise<WorkflowRead[]> {
  return request.get('/workflows', undefined, '/api', { showLoading: false })
}

export function getWorkflow(id: number): Promise<WorkflowRead> {
  return request.get(`/workflows/${id}`, undefined, '/api', { showLoading: false })
}

export function createWorkflow(payload: Partial<WorkflowRead> & { name: string; definition_json?: any }): Promise<WorkflowRead> {
  return request.post('/workflows', payload, '/api', { showLoading: false })
}

export function updateWorkflow(id: number, payload: WorkflowUpdate): Promise<WorkflowRead> {
  return request.put(`/workflows/${id}`, payload, '/api', { showLoading: false })
}

export function deleteWorkflow(id: number): Promise<void> {
  return request.delete(`/workflows/${id}`, undefined, '/api', { showLoading: false })
}

export function deleteRun(runId: number): Promise<{ ok: boolean; message: string }> {
  return request.delete(`/workflows/runs/${runId}`, undefined, '/api')
}

export interface ValidationError {
  line: number
  variable: string
  error_type: string
  message: string
  suggestion?: string
}

export interface ValidationResult {
  is_valid: boolean
  errors: ValidationError[]
  warnings: ValidationError[]
}

export function validateWorkflow(id: number): Promise<ValidationResult> {
  return request.post(`/workflows/${id}/validate`, {}, '/api', { showLoading: false })
}


export interface WorkflowNodePort {
  name: string
  type: string
  description: string
  required?: boolean
}

export interface WorkflowNodeType {
  type: string
  category: string
  label: string
  description: string
  inputs: WorkflowNodePort[]
  outputs: WorkflowNodePort[]
  config_schema: any
}

export function getNodeTypes(): Promise<{ node_types: WorkflowNodeType[] }> {
  return request.get('/nodes/types', undefined, '/api', { showLoading: false })
}



// ============================================================
// ============================================================

export function getRun(runId: number): Promise<WorkflowRunRead> {
  return request.get(`/workflows/runs/${runId}`, undefined, '/api', { showLoading: false })
}

export function listAllRuns(params?: { limit?: number; offset?: number; status?: string }): Promise<WorkflowRunRead[]> {
  return request.get('/runs', params, '/api', { showLoading: false })
}

export function cancelRun(runId: number): Promise<{ ok: boolean; message?: string }> {
  return request.post(`/workflows/runs/${runId}/cancel`, {}, '/api')
}

// ============================================================
// ============================================================

export interface WorkflowStatement {
  variable: string
  code: string
}

export interface ProgressEvent {
  type: 'progress'
  statement: WorkflowStatement
  percent: number
  message: string
  stage?: string
}

export interface CompleteEvent {
  type: 'complete'
  statement: WorkflowStatement
  result: any
}

export interface ErrorEvent {
  type: 'error'
  statement: WorkflowStatement
  error: string
}

export interface StartEvent {
  type: 'start'
  statement: WorkflowStatement
}

export type WorkflowStreamEvent = StartEvent | ProgressEvent | CompleteEvent | ErrorEvent

export interface WorkflowStreamCallbacks {
  onRunStarted?: (runId: number) => void
  onStart?: (event: StartEvent) => void
  onProgress?: (event: ProgressEvent) => void
  onComplete?: (event: CompleteEvent) => void
  onError?: (event: ErrorEvent) => void
  onEnd?: () => void
}

export async function runCodeWorkflowStream(
  workflowId: number,
  callbacks: WorkflowStreamCallbacks,
  resume: boolean = false,
  runId?: number
): Promise<{ runId: { value: number }; eventSource: EventSource }> {

  let url = `${API_BASE_URL}/workflows/${workflowId}/execute-stream`
  if (resume && runId) {
    url += `?resume=true&run_id=${runId}`
  }


  const eventSource = new EventSource(url)
  const runIdRef = { value: runId || 0 }

  eventSource.onopen = () => {
  }

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'run_started':
          runIdRef.value = data.run_id
          callbacks.onRunStarted?.(runIdRef.value)
          break

        case 'start':
          callbacks.onStart?.(data as StartEvent)
          break

        case 'progress':
          callbacks.onProgress?.(data as ProgressEvent)
          break

        case 'complete':
          callbacks.onComplete?.(data as CompleteEvent)
          break

        case 'error':
          callbacks.onError?.(data as ErrorEvent)
          break

        case 'paused':
          callbacks.onEnd?.()
          eventSource.close()
          break

        case 'end':
          callbacks.onEnd?.()
          eventSource.close()
          break

        default:
      }
    } catch (error) {
    }
  }

  eventSource.onerror = (error) => {

    if (eventSource.readyState === EventSource.CLOSED) {
      return
    }

    eventSource.close()

    callbacks.onError?.({
      type: 'error',
      statement: { variable: 'unknown', code: 'unknown' },
      error: 'SSE connection error'
    })
    callbacks.onEnd?.()
  }

  return { runId: runIdRef, eventSource }
}

export async function parseWorkflowCode(code: string): Promise<{
  success: boolean
  statements?: WorkflowStatement[]
  errors?: string[]
}> {
  return request.post('/workflows/parse', { code }, '/api', { showLoading: false })
}

export async function saveCodeWorkflow(name: string, code: string): Promise<WorkflowRead> {
  return request.post('/workflows/code', { name, code }, '/api')
}

export async function getCodeWorkflow(id: number): Promise<{ id: number; name: string; code: string; revision?: string; keep_run_history?: boolean }> {
  return request.get(`/workflows/${id}/code`, undefined, '/api', { showLoading: false })
}

export interface ProjectTemplate {
  workflow_id: number
  workflow_name: string
  template: string | null
  description?: string
}

export function getProjectTemplates(): Promise<{ templates: ProjectTemplate[] }> {
  return request.get('/workflows/project-templates', undefined, '/api', { showLoading: false })
}
