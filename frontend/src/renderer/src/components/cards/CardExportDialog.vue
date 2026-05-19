<template>
  <el-dialog v-model="visible" :title="t('card_export.title')" width="560px" destroy-on-close>
    <el-form label-position="top">
      <el-form-item :label="t('card_export.scope')">
        <el-radio-group v-model="scope">
          <el-radio value="all">{{ t('card_export.scope_all') }}</el-radio>
          <el-radio value="single">{{ t('card_export.scope_single') }}</el-radio>
          <el-radio value="type">{{ t('card_export.scope_type') }}</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="scope === 'single'" :label="t('card_export.select_card')">
        <el-select v-model="selectedCardId" :placeholder="t('card_export.select_card_placeholder')" filterable style="width: 100%">
          <el-option
            v-for="card in cards"
            :key="card.id"
            :label="`${card.title}（${card.card_type.name}）`"
            :value="card.id!"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="scope === 'type'" :label="t('card_export.select_card_type')">
        <el-select v-model="selectedTypeId" :placeholder="t('card_export.select_type_placeholder')" style="width: 100%">
          <el-option
            v-for="type in cardTypes"
            :key="type.id"
            :label="type.name"
            :value="type.id!"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="t('card_export.format')">
        <el-select v-model="format" style="width: 100%">
          <el-option :label="t('card_export.format_txt')" value="txt" />
          <el-option :label="t('card_export.format_md')" value="md" />
          <el-option :label="t('card_export.format_json')" value="json" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-alert :title="summaryText" type="info" :closable="false" show-icon />

    <template #footer>
      <el-button @click="visible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="exporting" :disabled="!canExport" @click="handleExport">
        {{ t('card_export.export') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { exportCardsForProject, type CardExportFormat, type CardExportScope } from '@renderer/api/cards'
import type { components } from '@renderer/types/generated'
import { useI18n } from 'vue-i18n'

type CardRead = components['schemas']['CardRead']
type CardTypeRead = components['schemas']['CardTypeRead']

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
  projectId?: number
  projectName?: string
  cards: CardRead[]
  cardTypes: CardTypeRead[]
  initialCardId?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const scope = ref<CardExportScope>('all')
const selectedCardId = ref<number | null>(null)
const selectedTypeId = ref<number | null>(null)
const format = ref<CardExportFormat>('txt')
const exporting = ref(false)

const filteredCards = computed<CardRead[]>(() => {
  if (scope.value === 'all') return props.cards
  if (scope.value === 'single') {
    return props.cards.filter(card => card.id === selectedCardId.value)
  }
  return props.cards.filter(card => card.card_type_id === selectedTypeId.value)
})

const canExport = computed(() => {
  if (!props.projectId) return false
  if (scope.value === 'single' && !selectedCardId.value) return false
  if (scope.value === 'type' && !selectedTypeId.value) return false
  return filteredCards.value.length > 0
})

const summaryText = computed(() => {
  if (filteredCards.value.length === 0) return t('card_export.no_cards_match')
  return t('card_export.summary', { count: filteredCards.value.length, format: format.value.toUpperCase() })
})

watch(
  () => props.modelValue,
  isVisible => {
    if (!isVisible) return

    format.value = 'txt'
    selectedCardId.value = null
    selectedTypeId.value = null

    if (props.initialCardId && props.cards.some(card => card.id === props.initialCardId)) {
      scope.value = 'single'
      selectedCardId.value = props.initialCardId
    } else {
      scope.value = 'all'
    }

    if (selectedCardId.value == null && props.cards.length > 0) {
      selectedCardId.value = props.cards[0].id!
    }
    if (props.cardTypes.length > 0) {
      selectedTypeId.value = props.cardTypes[0].id!
    }
  },
  { immediate: true }
)

watch(scope, newScope => {
  if (newScope === 'single' && selectedCardId.value == null && props.cards.length > 0) {
    selectedCardId.value = props.cards[0].id!
  }
  if (newScope === 'type' && selectedTypeId.value == null && props.cardTypes.length > 0) {
    selectedTypeId.value = props.cardTypes[0].id!
  }
})

function safeSegment(value: string): string {
  return (value || 'novelforge')
    .trim()
    .replace(/[<>:"/\\|?*]/g, '_')
    .replace(/\s+/g, '_')
}

function buildFallbackFilename(): string {
  const projectName = safeSegment(props.projectName || 'novelforge')
  const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z')
  return `${projectName}-cards-${scope.value}-${timestamp}.${format.value}`
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.style.display = 'none'
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

async function handleExport() {
  if (!props.projectId || !canExport.value) return

  const payload: any = {
    scope: scope.value,
    format: format.value,
  }
  if (scope.value === 'single') payload.card_id = selectedCardId.value
  if (scope.value === 'type') payload.card_type_id = selectedTypeId.value

  exporting.value = true
  try {
    const response = await exportCardsForProject(props.projectId, payload)
    const filename = response.filename || buildFallbackFilename()
    triggerDownload(response.blob, filename)
    ElMessage.success(t('card_export.messages.export_success', { count: filteredCards.value.length }))
    visible.value = false
  } catch (error) {
    console.error('export failed:', error)
  } finally {
    exporting.value = false
  }
}
</script>
