<template>
  <el-form-item :label="label" :prop="prop">
    <el-input
      v-if="!isLongText"
      :model-value="modelValue"
      @update:modelValue="emit('update:modelValue', $event)"
      :placeholder="placeholder"
      clearable
    />
    <el-input
      v-else
      type="textarea"
      :model-value="modelValue"
      @update:modelValue="emit('update:modelValue', $event)"
      :placeholder="placeholder"
      :autosize="{ minRows: 3, maxRows: 10 }"
      clearable
    />
  </el-form-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import type { JSONSchema } from '@renderer/api/schema'

const props = defineProps<{
  modelValue: string | undefined
  label: string
  prop: string
  schema: JSONSchema
}>()

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const localeStore = useLocaleStore()
const legacyText = (...codes: number[]) => String.fromCharCode(...codes)
const longTextHints = [
  'thinking',
  'process',
  'description',
  'overview',
  'content',
  legacyText(24605, 32771),
  legacyText(36807, 31243),
  legacyText(25551, 36848),
  legacyText(27010, 36848)
]

const isLongText = computed(() => {
  if (props.schema.minLength !== undefined && props.schema.minLength > 50) {
    return true
  }
  const description = props.schema.description?.toLowerCase() || ''
  const title = props.schema.title?.toLowerCase() || ''
  if (props.prop === 'overview' || props.prop === 'content') return true
  return longTextHints.some(hint => description.includes(hint) || title.includes(hint))
})

const placeholder = computed(() => {
  return props.schema.description ? String(props.schema.description) : t('dynamic_form.fields.input_placeholder', { label: props.label })
})
</script>
