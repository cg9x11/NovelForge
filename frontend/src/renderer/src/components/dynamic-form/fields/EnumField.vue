<template>
  <el-form-item :label="label" :prop="prop">
    <el-select
      :model-value="modelValue"
      @update:modelValue="emit('update:modelValue', $event)"
      :placeholder="placeholder"
      :loading="isLoading"
      :no-data-text="noDataText"
      clearable
      style="width: 100%"
    >
      <el-option
        v-for="item in resolvedOptions"
        :key="String(item)"
        :label="getOptionLabel(item)"
        :value="item"
      />
    </el-select>
  </el-form-item>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { JSONSchema } from '@renderer/api/schema'
import { resolveKnowledgeOptions } from '@renderer/services/knowledgeOptionResolver'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import { translateText } from '@renderer/locales/runtimeTranslations'

const props = defineProps<{
  modelValue: string | number | undefined
  label: string
  prop: string
  schema: JSONSchema
}>()

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const localeStore = useLocaleStore()
const cjkRe = /[\u4e00-\u9fff]/
const knowledgeOptions = ref<Array<string | number>>([])
const isLoading = ref(false)


watch(
  () => props.schema['x-knowledge-source'],
  async (knowledgeName) => {
    if (!knowledgeName) {
      knowledgeOptions.value = []
      return
    }

    isLoading.value = true
    knowledgeOptions.value = await resolveKnowledgeOptions(knowledgeName)
    isLoading.value = false
  },
  { immediate: true }
)

const resolvedOptions = computed(() => {
  const baseOptions = (props.schema.enum && props.schema.enum.length > 0)
    ? props.schema.enum
    : knowledgeOptions.value

  if (
    props.modelValue !== undefined
    && props.modelValue !== null
    && props.modelValue !== ''
    && !baseOptions.includes(props.modelValue)
  ) {
    return [props.modelValue, ...baseOptions]
  }

  return baseOptions
})

function cleanDisplayText(value: string): string {
  return cjkRe.test(value) ? '' : value
}

const placeholder = computed(() => {
  return props.schema.description ? cleanDisplayText(translateText(String(props.schema.description), localeStore.locale)) : t('dynamic_form.fields.select_placeholder', { label: props.label })
})

const noDataText = computed(() => {
  if (isLoading.value) {
    return t('dynamic_form.fields.loading_options')
  }
  if (props.schema['x-knowledge-source']) {
    return t('dynamic_form.fields.no_knowledge_options')
  }
  return t('dynamic_form.fields.no_options')
})

function getOptionLabel(item: string | number): string {
  const raw = String(item)
  if (props.prop === 'entity_type') {
    return t(`dynamic_form.fields.entity.${raw}`) || raw
  }
  return translateText(raw, localeStore.locale)
}
</script>
