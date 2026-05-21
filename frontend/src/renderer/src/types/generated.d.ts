export interface paths {
  [path: string]: any
}

export type webhooks = Record<string, never>

export interface components {
  schemas: Record<string, any>
  responses: Record<string, any>
  parameters: Record<string, any>
  requestBodies: Record<string, any>
  headers: Record<string, any>
  pathItems: Record<string, any>
}

export type $defs = Record<string, never>

export interface operations {
  [operation: string]: any
}
