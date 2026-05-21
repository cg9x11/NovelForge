import { API_BASE_URL } from './request'
import { i18n } from '@renderer/i18n'

import type {
  InstructionGenerateRequest,
  StreamEvent,
  Instruction
} from '@renderer/types/instruction'

export interface GenerateParams extends InstructionGenerateRequest {
}

export interface GenerateCallbacks {
  onThinking?: (text: string) => void
  onInstruction?: (instruction: Instruction) => void
  onWarning?: (text: string) => void
  onError?: (text: string) => void
  onDone?: (success: boolean, message?: string, finalData?: any) => void
}

export async function generateWithInstructionStream(
  params: GenerateParams,
  callbacks: GenerateCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE_URL}/ai/generate/stream`

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params),
      signal
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    if (!response.body) {
      throw new Error(String(i18n.global.t('generation.errors.empty_response')))
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim()) {
          continue
        }

        const event = parseSSELine(line)
        if (event) {
          handleEvent(event, callbacks)
        }
      }
    }

    if (buffer.trim()) {
      const event = parseSSELine(buffer)
      if (event) {
        handleEvent(event, callbacks)
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Generation aborted')
      return
    }

    console.error('Generation failed:', error)
    callbacks.onError?.(error.message || String(i18n.global.t('generation.errors.failed')))
  }
}

function parseSSELine(line: string): { event: string; data: any } | null {

  let eventType = 'message'
  let dataStr = ''

  const lines = line.split('\n')
  for (const l of lines) {
    if (l.startsWith('event:')) {
      eventType = l.slice(6).trim()
    } else if (l.startsWith('data:')) {
      dataStr = l.slice(5).trim()
    }
  }

  if (!dataStr) {
    return null
  }

  try {
    const data = JSON.parse(dataStr)
    return { event: eventType, data }
  } catch (e) {
    console.warn('Failed to parse SSE data:', dataStr)
    return null
  }
}

function formatGenerationStreamError(data: any): string {
  if (data?.error_code === 'GENERATION_FAILED') {
    const message = data.message ? `: ${data.message}` : ''
    return `${i18n.global.t('generation.errors.failed')}${message}`
  }
  return data?.text || data?.message || String(i18n.global.t('generation.errors.failed'))
}

function handleEvent(event: { event: string; data: any }, callbacks: GenerateCallbacks): void {
  const { data } = event
  const type = data.type || event.event

  switch (type) {
    case 'thinking':
      callbacks.onThinking?.(data.text)
      break

    case 'instruction':
      callbacks.onInstruction?.(data.instruction)
      break

    case 'warning':
      callbacks.onWarning?.(data.text)
      break

    case 'error':
      callbacks.onError?.(formatGenerationStreamError(data))
      break

    case 'done':
      callbacks.onDone?.(data.success !== false, data.message, data.final_data)
      break

    default:
      console.warn('Unknown event type:', type, data)
  }
}
