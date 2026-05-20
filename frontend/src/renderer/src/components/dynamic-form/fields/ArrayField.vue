<template>
  <el-card class="array-field-card" shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ label }}</span>
      </div>
    </template>

    <div v-if="!modelValue || modelValue.length === 0" class="empty-state">
      <p>{{ t('arrayField.empty') }}</p>
    </div>

    <div v-for="(item, index) in modelValue" :key="index" class="array-item">
      <div class="array-item-content">
        <component
          v-if="isSimpleTypeForIndex(index)"
          :is="getSimpleFieldComponentForIndex(index)"
          :label="t('arrayField.itemLabel', { index: index + 1 })"
          :prop="String(index)"
          :schema="getItemSchemaForIndex(index)"
          :model-value="item"
          @update:modelValue="updateItem(index, $event)"
        />
        <TupleField
          v-else-if="isTupleTypeForIndex(index)"
          :label="t('arrayField.itemLabel', { index: index + 1 })"
          :prop="String(index)"
          :schema="getItemSchemaForIndex(index)"
          :model-value="item"
          @update:modelValue="updateItem(index, $event)"
        />
        <ModelDrivenForm
          v-else
          :schema="getItemSchemaForIndex(index)"
          :model-value="item"
          :display-name-map="displayNameMap"
          @update:modelValue="updateItem(index, $event)"
        />
      </div>
      <div class="array-item-actions">
        <el-button
          type="danger"
          :icon="Delete"
          circle
          plain
          size="small"
          @click="removeItem(index)"
        />
      </div>
    </div>
    <el-button type="primary" :icon="Plus" plain @click="addItem" class="add-button">
      {{ t('arrayField.add') }} {{ addItemLabel }}
    </el-button>
  </el-card>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import { translateText } from '@renderer/locales/runtimeTranslations'
import { useI18n } from 'vue-i18n'
import type { JSONSchema } from '@renderer/api/schema'
import { Delete, Plus } from '@element-plus/icons-vue'
import { resolveActualSchema } from '@renderer/services/schemaFieldParser'

const { t } = useI18n()
const localeStore = useLocaleStore()
const ModelDrivenForm = defineAsyncComponent(() => import('../ModelDrivenForm.vue'))
const StringField = defineAsyncComponent(() => import('./StringField.vue'))
const NumberField = defineAsyncComponent(() => import('./NumberField.vue'))
const BooleanField = defineAsyncComponent(() => import('./BooleanField.vue'))
const TupleField = defineAsyncComponent(() => import('./TupleField.vue'))

const props = defineProps<{
  modelValue: any[] | undefined
  label: string
  schema: JSONSchema
  displayNameMap?: Record<string, string>
  readonly?: boolean
  contextData?: Record<string, any>
  ownerId?: number | null
}>()

const emit = defineEmits(['update:modelValue'])


const addItemLabel = computed(() => {
  const raw = (props.displayNameMap && props.displayNameMap[itemSchema.value.title || '']) || itemSchema.value.title || t('arrayField.newItem')
  return translateText(String(raw), localeStore.locale)
})

const itemSchema = computed((): JSONSchema => {
  if (props.schema.items) {
    return resolveActualSchema(props.schema.items, props.schema)
  }
  return { type: 'string', title: t('arrayField.item') }
})

function getItemSchemaForIndex(index: number): JSONSchema {
  const base = itemSchema.value
  const value = (props.modelValue || [])[index]
  if ((base as any).anyOf) {
    const matched = resolveAnyOfForValue(base, value)
    if (matched) return matched
  }
  return base
}

function isSimpleTypeForIndex(index: number) {
  const actualSchema = getItemSchemaForIndex(index)
  return actualSchema.type === 'string' || actualSchema.type === 'number' || actualSchema.type === 'integer' || actualSchema.type === 'boolean'
}

function isTupleTypeForIndex(index: number) {
  const actualSchema = getItemSchemaForIndex(index) as any
  if (!actualSchema || actualSchema.type !== 'array') return false
  return Array.isArray(actualSchema.prefixItems) || Array.isArray(actualSchema.anyOf)
}

function getSimpleFieldComponentForIndex(index: number) {
  const actualSchema = getItemSchemaForIndex(index)
  switch (actualSchema.type) {
    case 'string':
      return StringField
    case 'number':
    case 'integer':
      return NumberField
    case 'boolean':
      return BooleanField
    default:
      return StringField
  }
}

function updateItem(index: number, newItem: any) {
  const newArray = [...(props.modelValue || [])]
  newArray[index] = newItem
  emit('update:modelValue', newArray)
}

function removeItem(index: number) {
  const newArray = [...(props.modelValue || [])]
  newArray.splice(index, 1)
  emit('update:modelValue', newArray)
}

function addItem() {
  const newArray = [...(props.modelValue || [])]
  const base = itemSchema.value
  let defaultValue: any

  if ((base as any).anyOf) {
    defaultValue = { name: '', entity_type: 'character', life_span: '短期' }
  } else {
    defaultValue = createArrayItemDefaultValue(base)
  }

  newArray.push(defaultValue)
  emit('update:modelValue', newArray)
}

function createArrayItemDefaultValue(schema: JSONSchema): any {
  const actualSchema = resolveActualSchema(schema, props.schema)

  if (actualSchema.default !== undefined) {
    return actualSchema.default
  }

  switch (actualSchema.type) {
    case 'string': return ''
    case 'number':
    case 'integer': return 0
    case 'boolean': return false
    case 'array': return []
    case 'object': return {}
    default: return null
  }
}

function resolveAnyOfForValue(base: JSONSchema, value: any): JSONSchema | null {
  if (!base.anyOf) return null
  const nonNullSchema = base.anyOf.find((s: any) => s && s.type !== 'null')
  return nonNullSchema ? resolveActualSchema(nonNullSchema as JSONSchema, props.schema) : null
}
</script>

<style scoped>
.array-field-card {
  margin-top: 10px;
  margin-bottom: 20px;
  background-color: var(--el-fill-color-lighter);
}
.empty-state {
  text-align: center;
  color: var(--el-text-color-secondary);
  padding: 20px 0;
}
.array-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
  padding: 15px;
  border: 1px dashed var(--el-border-color);
  border-radius: 4px;
}
.array-item-content {
  flex-grow: 1;
  padding-right: 15px;
}
.array-item-actions {
  flex-shrink: 0;
}
.add-button {
  margin-top: 10px;
  width: 100%;
}
</style>

