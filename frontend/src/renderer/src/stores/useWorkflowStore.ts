import { defineStore } from 'pinia'
import { i18n } from '@renderer/i18n'
import { ref, computed } from 'vue'
import {
    getRun,
    runCodeWorkflowStream,
    getNodeTypes,
    type WorkflowStreamCallbacks,
    type WorkflowNodeType
} from '@/api/workflows'

export interface RunInfo {
    id: number
    workflow_id: number
    workflow_name?: string
    status: string
    created_at?: string
    error?: string
    current_node?: string
    progress?: number
}

interface SSEConnection {
    runId: number
    workflowId: number
    workflowName: string
    eventSource: EventSource
    callbacks: WorkflowStreamCallbacks
}

export const useWorkflowStore = defineStore('workflow', () => {
    const nodeTypes = ref<WorkflowNodeType[]>([])
    const cardTypes = ref<any[]>([])
    const isLoadingNodeTypes = ref(false)

    // Getters
    const categories = computed(() => {
        const cats = new Set(nodeTypes.value.map(n => n.category))
        return Array.from(cats)
    })

    const getNodesByCategory = (category: string) => {
        return nodeTypes.value.filter(n => n.category === category)
    }

    const getNodeType = (type: string) => {
        return nodeTypes.value.find(n => n.type === type)
    }

    // Actions
    async function fetchNodeTypes() {
        if (isLoadingNodeTypes.value) return

        try {
            isLoadingNodeTypes.value = true
            const res = await getNodeTypes()
            nodeTypes.value = res.node_types
        } catch (error) {
            console.error('Failed to fetch node types:', error)
        } finally {
            isLoadingNodeTypes.value = false
        }
    }

    async function fetchCardTypes() {
        if (cardTypes.value.length > 0) return // cache
        try {
            const { getCardTypes } = await import('../api/cards')
            cardTypes.value = await getCardTypes()
        } catch (error) {
            console.error('Failed to fetch card types:', error)
        }
    }

    const runs = ref<Map<number, RunInfo>>(new Map())
    const pollingTimer = ref<any>(null)
    const sseConnections = ref<Map<number, SSEConnection>>(new Map())

    // Getters
    const activeRuns = computed(() => {
        return Array.from(runs.value.values()).filter(r =>
            ['pending', 'running', 'paused'].includes(r.status)
        ).sort((a, b) => b.id - a.id)
    })

    const completedRuns = computed(() => {
        return Array.from(runs.value.values()).filter(r =>
            ['succeeded', 'failed', 'cancelled', 'timeout'].includes(r.status)
        ).sort((a, b) => b.id - a.id)
    })

    const totalRunCount = computed(() => runs.value.size)
    const activeRunCount = computed(() => activeRuns.value.length)

    // Actions
    function addRun(id: number, workflowName?: string) {
        if (runs.value.has(id)) return

        runs.value.set(id, {
            id,
            workflow_id: 0,
            status: 'running',
            workflow_name: workflowName || String(i18n.global.t('workflow_store.loading')),
            progress: 0
        })

        fetchRunDetails(id)

        startPolling()
    }

    function updateRunProgress(id: number, progress: number, currentNode?: string) {
        const run = runs.value.get(id)
        if (run) {
            runs.value.set(id, {
                ...run,
                progress,
                current_node: currentNode
            })
        }
    }

    function updateRunStatus(id: number, status: string, error?: string) {
        const run = runs.value.get(id)
        if (run) {
            runs.value.set(id, {
                ...run,
                status,
                error
            })
        }
    }

    async function fetchRunDetails(id: number) {
        try {
            const run = await getRun(id)
            if (run) {
                const existingRun = runs.value.get(id)

                let errorMessage: string | undefined
                if (run.error_json) {
                    errorMessage = typeof run.error_json === 'object'
                        ? JSON.stringify(run.error_json)
                        : String(run.error_json)
                }

                runs.value.set(id, {
                    id: run.id,
                    workflow_id: run.workflow_id,
                    workflow_name: run.workflow?.name || String(i18n.global.t('workflow_store.unnamed')),
                    status: run.status,
                    created_at: run.created_at || undefined,
                    error: errorMessage,
                    current_node: existingRun?.current_node,
                    progress: existingRun?.progress
                })
            }
        } catch (e) {
            console.error(`Failed to fetch run ${id}`, e)
        }
    }

    function startPolling() {
        if (pollingTimer.value) return

        checkActiveRuns()

        pollingTimer.value = setInterval(() => {
            checkActiveRuns()
        }, 2000)
    }

    function stopPolling() {
        if (pollingTimer.value) {
            clearInterval(pollingTimer.value)
            pollingTimer.value = null
        }
    }

    function setupWorkflowListener() {
        const handleWorkflowStarted = (event: CustomEvent) => {
            const runIds = event.detail as number[]

            runIds.forEach(runId => {
                if (!runs.value.has(runId)) {
                    addRun(runId, String(i18n.global.t('workflow_store.trigger_workflow')))
                }
            })
        }

        window.addEventListener('workflow-started', handleWorkflowStarted as EventListener)

        return () => {
            window.removeEventListener('workflow-started', handleWorkflowStarted as EventListener)
        }
    }

    async function checkActiveRuns() {
        if (activeRuns.value.length === 0) {
            stopPolling()
            return
        }

        for (const run of activeRuns.value) {
            await fetchRunDetails(run.id)
        }
    }

    function clearCompleted() {
        const completedIds = completedRuns.value.map(r => r.id)
        completedIds.forEach(id => {
            runs.value.delete(id)
            const conn = sseConnections.value.get(id)
            if (conn) {
                conn.eventSource.close()
                sseConnections.value.delete(id)
            }
        })
    }

    async function startWorkflowExecution(
        workflowId: number,
        workflowName: string,
        callbacks: WorkflowStreamCallbacks,
        resume: boolean = false,
        runId?: number
    ) {
        let currentRunId: number | null = runId || null
        let totalNodes = 0
        let completedNodes = 0

        if (resume && runId) {
            const existingRun = runs.value.get(runId)
            if (existingRun) {
                updateRunStatus(runId, 'running')
            } else {
                addRun(runId, workflowName)
            }
        }

        const wrappedCallbacks: WorkflowStreamCallbacks = {
            onRunStarted: (actualRunId: number) => {
                currentRunId = actualRunId
                if (!resume) {
                    addRun(actualRunId, workflowName)
                }
                if (callbacks.onRunStarted) {
                    callbacks.onRunStarted(actualRunId)
                }
            },

            onStart: (event) => {
                totalNodes++
                if (currentRunId) {
                    const progress = totalNodes > 0 ? (completedNodes / totalNodes) * 100 : 0
                    updateRunProgress(currentRunId, progress, event.statement?.variable)
                }
                if (callbacks.onStart) {
                    callbacks.onStart(event)
                }
            },

            onProgress: (event) => {
                if (currentRunId) {
                    const nodeProgress = event.percent || 0
                    const overallProgress = totalNodes > 0
                        ? ((completedNodes + nodeProgress / 100) / totalNodes) * 100
                        : nodeProgress
                    updateRunProgress(currentRunId, overallProgress, event.statement?.variable)
                }
                if (callbacks.onProgress) {
                    callbacks.onProgress(event)
                }
            },

            onComplete: (event) => {
                completedNodes++
                if (currentRunId) {
                    const progress = totalNodes > 0 ? (completedNodes / totalNodes) * 100 : 100
                    updateRunProgress(currentRunId, progress, event.statement?.variable)
                }
                if (callbacks.onComplete) {
                    callbacks.onComplete(event)
                }
            },

            onError: (event) => {
                if (currentRunId) {
                    updateRunStatus(currentRunId, 'failed', event.error)
                }
                if (callbacks.onError) {
                    callbacks.onError(event)
                }
            },

            onEnd: () => {
                if (currentRunId) {
                    updateRunProgress(currentRunId, 100, undefined)
                    const run = runs.value.get(currentRunId)
                    if (run && run.status !== 'failed') {
                        updateRunStatus(currentRunId, 'succeeded')
                    }
                    const conn = sseConnections.value.get(currentRunId)
                    if (conn) {
                        conn.eventSource.close()
                        sseConnections.value.delete(currentRunId)
                    }
                }
                if (callbacks.onEnd) {
                    callbacks.onEnd()
                }
            }
        }

        try {
            if (resume && runId) {
                const oldConn = sseConnections.value.get(runId)
                if (oldConn) {
                    oldConn.eventSource.close()
                    sseConnections.value.delete(runId)
                }
            }

            const { runId: actualRunId, eventSource } = await runCodeWorkflowStream(
                workflowId,
                wrappedCallbacks,
                resume,
                runId
            )

            if (currentRunId) {
                sseConnections.value.set(currentRunId, {
                    runId: currentRunId,
                    workflowId,
                    workflowName,
                    eventSource,
                    callbacks: wrappedCallbacks
                })
            }

            return { runId: actualRunId, eventSource }
        } catch (error) {
            throw error
        }
    }

    function pauseWorkflowExecution(runId: number) {
        const conn = sseConnections.value.get(runId)
        if (conn) {
            conn.eventSource.close()
            sseConnections.value.delete(runId)
            updateRunStatus(runId, 'paused')
        } else {
        }
    }

    function getSSEConnection(runId: number) {
        return sseConnections.value.get(runId)
    }

    return {
        nodeTypes,
        cardTypes,
        isLoadingNodeTypes,
        categories,
        getNodesByCategory,
        getNodeType,
        fetchNodeTypes,
        fetchCardTypes,

        runs,
        activeRuns,
        completedRuns,
        activeRunCount,
        totalRunCount,
        addRun,
        updateRunProgress,
        updateRunStatus,
        clearCompleted,
        startWorkflowExecution,
        pauseWorkflowExecution,
        getSSEConnection,

        setupWorkflowListener
    }
})
