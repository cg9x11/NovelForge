import request from './request'
import { ref } from 'vue'

export interface JSONSchema {
  // Common properties
  type?: string | string[]
  title?: string
  description?: string
  default?: any
  examples?: any[]
  enum?: any[]
  const?: any
  minLength?: number
  'x-knowledge-source'?: string

  // Object properties
  properties?: { [key: string]: JSONSchema }
  required?: string[]
  items?: JSONSchema
  prefixItems?: JSONSchema[]
  anyOf?: JSONSchema[]
  $ref?: string
}

const schemas = ref<Map<string, JSONSchema>>(new Map())
const isLoading = ref(false)
const error = ref<any>(null)


function resolveRef(refPath: string, allSchemas: Map<string, JSONSchema>): JSONSchema | null {
  const refName = refPath.split('/').pop()
  if (!refName) {
    console.error('Invalid $ref path:', refPath)
    return null
  }
  const resolved = allSchemas.get(refName)
  if (!resolved) {
    console.error(`Unable to resolve $ref in allSchemas: ${refName}`)
        return null
      }
  return resolved
}

function dereferenceSchema(
  schema: JSONSchema,
  allSchemas: Map<string, JSONSchema>,
  visited = new Set<string>()
): JSONSchema {
  if (typeof schema !== 'object' || schema === null) {
    return schema
  }

  if (schema.$ref) {
    if (visited.has(schema.$ref)) {
      console.warn('Circular reference detected:', schema.$ref)
      return { type: 'object', title: 'Circular Reference' }
    }
    visited.add(schema.$ref)
    const resolved = resolveRef(schema.$ref, allSchemas)
    if (resolved) {
      return dereferenceSchema(resolved, allSchemas, visited)
    } else {
      return { type: 'string', title: `Unresolved Reference: ${schema.$ref}` }
    }
  }

  const newSchema = { ...schema }
  if (newSchema.properties) {
    newSchema.properties = Object.fromEntries(
      Object.entries(newSchema.properties).map(([key, propSchema]) => [
        key,
        dereferenceSchema(propSchema, allSchemas, new Set(visited))
      ])
    )
  }

  if (newSchema.items) {
    newSchema.items = dereferenceSchema(newSchema.items, allSchemas, new Set(visited))
  }

  if (newSchema.prefixItems) {
    newSchema.prefixItems = newSchema.prefixItems.map(itemSchema =>
      dereferenceSchema(itemSchema, allSchemas, new Set(visited))
    );
  }

  if (newSchema.anyOf) {
    newSchema.anyOf = newSchema.anyOf.map(itemSchema =>
      dereferenceSchema(itemSchema, allSchemas, new Set(visited))
    );
  }

  return newSchema
}


async function loadSchemas() {
  if (schemas.value.size > 0 || isLoading.value) {
    return
  }
  isLoading.value = true
  error.value = null
  try {
    const allSchemas = await request.get<Record<string, JSONSchema>>('/ai/schemas')
    if (allSchemas) {
      const schemaMap = new Map<string, JSONSchema>(Object.entries(allSchemas))

      const dereferencedSchemaMap = new Map<string, JSONSchema>()

      for (const [name, schema] of schemaMap.entries()) {
        dereferencedSchemaMap.set(name, schema);
      }

      for (const [name, schema] of dereferencedSchemaMap.entries()) {
        dereferencedSchemaMap.set(name, dereferenceSchema(schema, dereferencedSchemaMap));
      }

      // DEBUG: Log all the schema keys that were loaded
      console.log('[SchemaService] All schema keys loaded from /ai/schemas:', Array.from(dereferencedSchemaMap.keys()));

      schemas.value = dereferencedSchemaMap
    }
  } catch (e) {
    console.error('Failed to load schemas from /ai/schemas:', e)
    error.value = e
  } finally {
    isLoading.value = false
  }
}

async function refreshSchemas() {
  try {
    schemas.value = new Map()
    isLoading.value = false
    await loadSchemas()
  } catch (e) {
    console.error('Failed to refresh schemas:', e)
  }
}

function getSchema(name: string): JSONSchema | undefined {
  return schemas.value.get(name)
}

export const schemaService = {
  schemas,
  isLoading,
  error,
  loadSchemas,
  refreshSchemas,
  getSchema
}
