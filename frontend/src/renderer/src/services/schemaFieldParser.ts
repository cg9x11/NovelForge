
import { schemaService } from '@renderer/api/schema'


export interface ParsedField {
  name: string
  title: string
  type: string
  path: string
  description: string
  required: boolean
  expanded: boolean
  children?: ParsedField[]
  expandable?: boolean
  arrayItemType?: string
  hasChildren?: boolean
}

export function parseSchemaFields(schema: any, path = '$.content', maxDepth = 5): ParsedField[] {
  if (maxDepth <= 0) return []

  const fields: ParsedField[] = []
  try {
    const properties = schema.properties || {}
    const defs = schema.$defs || {}
    const required = schema.required || []

    for (const [fieldName, fieldSchema] of Object.entries(properties)) {
      if (typeof fieldSchema !== 'object' || !fieldSchema) continue

      const resolvedSchema = resolveSchemaRef(fieldSchema as any, defs)

      const fieldType = resolvedSchema.type || 'unknown'
      const fieldTitle = resolvedSchema.title || fieldName
      const fieldDescription = resolvedSchema.description || ''
      const fieldPath = `${path}.${fieldName}`

      const fieldInfo: ParsedField = {
        name: fieldName,
        title: fieldTitle,
        type: fieldType,
        path: fieldPath,
        description: fieldDescription,
        required: required.includes(fieldName),
        expanded: false
      }

      if (fieldType === 'object' && resolvedSchema.properties) {
        const children = parseSchemaFields(resolvedSchema, fieldPath, maxDepth - 1)
        if (children.length > 0) {
          fieldInfo.children = children
          fieldInfo.expandable = true
          fieldInfo.hasChildren = true
        }
      }

      else if (fieldType === 'array' && resolvedSchema.items) {
        const itemsSchema = resolveSchemaRef(resolvedSchema.items, defs)
        if (itemsSchema.type === 'object' && itemsSchema.properties) {
          const children = parseSchemaFields(itemsSchema, `${fieldPath}[0]`, maxDepth - 1)
          if (children.length > 0) {
            fieldInfo.children = children
            fieldInfo.expandable = true
            fieldInfo.hasChildren = true
            fieldInfo.arrayItemType = 'object'
          }
        } else {
          fieldInfo.arrayItemType = itemsSchema.type || 'unknown'
        }
      }

      fields.push(fieldInfo)
    }
  } catch (e) {
  }

  return fields
}

export function resolveSchemaRef(schema: any, localDefs?: any): any {
  if (!schema || typeof schema !== 'object') return schema

  if (schema.anyOf && Array.isArray(schema.anyOf)) {
    for (const anySchema of schema.anyOf) {
      if (anySchema.type === 'null') continue

      const resolved = resolveSchemaRef(anySchema, localDefs)
      if (resolved && resolved.type && resolved.type !== 'null') {
        return {
          ...resolved,
          title: schema.title || resolved.title,
          description: schema.description || resolved.description
        }
      }
    }
  }

  if (schema.$ref && typeof schema.$ref === 'string') {
    const refPath = schema.$ref
    if (refPath.startsWith('#/$defs/')) {
      const refName = refPath.replace('#/$defs/', '')

      let resolved = localDefs && localDefs[refName] ? localDefs[refName] : null

      if (!resolved) {
        resolved = schemaService.getSchema(refName)
      }

      if (resolved) {
        const finalResolved = resolveSchemaRef(resolved, localDefs)
        return {
          ...finalResolved,
          title: schema.title || finalResolved.title,
          description: schema.description || finalResolved.description
        }
      }
    }
  }

  return schema
}

export function getFieldIcon(type: string): string {
  switch (type) {
    case 'object': return '📁'
    case 'array': return '📊'
    case 'string': return '📄'
    case 'number':
    case 'integer': return '🔢'
    case 'boolean': return '☑️'
    default: return '📄'
  }
}

export function toggleFieldExpanded(fields: ParsedField[], targetPath: string): void {
  for (const field of fields) {
    if (field.path === targetPath) {
      field.expanded = !field.expanded
      return
    }
    if (field.children) {
      toggleFieldExpanded(field.children, targetPath)
    }
  }
}

export function extractFieldPathOptions(fields: ParsedField[], options: Array<{ label: string; value: string }> = []): Array<{ label: string; value: string }> {
  for (const field of fields) {
    if (field.type !== 'object' || !field.children?.length) {
      const label = field.path.replace(/^\$\.content\.?/, '') || field.name
      options.push({
        label: label,
        value: field.path
      })
    }

    if (field.children?.length) {
      extractFieldPathOptions(field.children, options)
    }
  }

  return options
}

export function resolveActualSchema(schema: any, parentSchema?: any): any {
  const localDefs = parentSchema?.$defs || {}
  const base = resolveSchemaRef(schema, localDefs)

  if (!base || typeof base !== 'object') return base

  const resolved: any = { ...base }

  if (resolved.properties && typeof resolved.properties === 'object') {
    const nextProps: Record<string, any> = {}
    for (const [key, val] of Object.entries(resolved.properties)) {
      nextProps[key] = resolveSchemaRef(val as any, localDefs)
    }
    resolved.properties = nextProps
  }

  if (resolved.items) {
    resolved.items = resolveSchemaRef(resolved.items, localDefs)
  }

  if (Array.isArray(resolved.prefixItems)) {
    resolved.prefixItems = resolved.prefixItems.map((it: any) => resolveSchemaRef(it, localDefs))
  }

  if (Array.isArray(resolved.anyOf)) {
    resolved.anyOf = resolved.anyOf.map((it: any) => resolveSchemaRef(it, localDefs))
  }

  return resolved
}

