

export type InstructionOp = 'set' | 'append' | 'done'

export interface InstructionBase {
  op: InstructionOp
}

export interface SetInstruction extends InstructionBase {
  op: 'set'
  path: string
  value: any
}

export interface AppendInstruction extends InstructionBase {
  op: 'append'
  path: string
  value: any
}

export interface DoneInstruction extends InstructionBase {
  op: 'done'
}

export type Instruction = SetInstruction | AppendInstruction | DoneInstruction


export interface GenerationConfig {
  mode?: 'instruction_stream'
  prompt_template?: string
  field_hints?: Record<string, string>
  field_order?: string[]
  custom?: Record<string, any>
}


export interface ConversationMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface InstructionGenerateRequest {
  llm_config_id: number
  user_prompt?: string
  response_model_schema: Record<string, any>
  current_data?: Record<string, any>
  conversation_context?: ConversationMessage[]
  generation_config?: GenerationConfig
  prompt_template?: string
  context_info?: string
  temperature?: number
  max_tokens?: number
  timeout?: number
  deps?: string
}


export interface ThinkingEvent {
  type: 'thinking'
  text: string
}

export interface InstructionEvent {
  type: 'instruction'
  instruction: Instruction
}

export interface WarningEvent {
  type: 'warning'
  text: string
}

export interface ErrorEvent {
  type: 'error'
  text: string
}

export interface DoneEvent {
  type: 'done'
  success?: boolean
  message?: string
}

export type StreamEvent = ThinkingEvent | InstructionEvent | WarningEvent | ErrorEvent | DoneEvent


export type GenerationMessageType = 'thinking' | 'action' | 'system' | 'user' | 'warning' | 'error'

export interface GenerationMessage {
  type: GenerationMessageType
  content: string
  timestamp: number
}
