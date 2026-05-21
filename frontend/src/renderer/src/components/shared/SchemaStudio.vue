<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="(v:boolean) => emit('update:visible', v)"
    :title="headerTitle"
    width="92%"
    top="4vh"
  >
    <div class="studio">
      <div class="left">
        <template v-if="mode==='type'">
          <el-form label-position="top" class="modelname-form">
            <el-form-item :label="t('schema_studio.model_name')">
              <el-input v-model="modelName" :placeholder="t('schema_studio.model_name_placeholder')" />
            </el-form-item>
          </el-form>
        </template>
        <div class="pane-header">{{ t('schema_studio.schema_builder') }}</div>
        <OutputModelBuilder v-model="builderFields" :models="relationTargets" :current-model-name="contextTitle" />
      </div>
      <div class="right">
        <div class="subpane">
          <div class="pane-header">{{ t('schema_studio.form_preview') }}</div>
          <div class="preview">
            <ModelDrivenForm v-if="schemaObject" :schema="schemaObject" v-model="previewModel" />
            <div v-else class="placeholder">{{ t('schema_studio.no_schema') }}</div>
          </div>
        </div>
        <div class="subpane">
          <div class="pane-header">{{ t('schema_studio.schema_json') }}</div>
          <el-input type="textarea" :rows="12" :model-value="schemaText" readonly />
        </div>
      </div>
    </div>
    <template #footer>
      <div class="footer-actions">
        <el-button @click="emit('update:visible', false)">{{ t('common.close') }}</el-button>
        <template v-if="mode==='card'">
          <el-button @click="restoreFollowType" type="warning" plain>{{ t('schema_studio.restore_follow_type') }}</el-button>
          <el-button @click="applyToType" type="primary" plain>{{ t('schema_studio.apply_to_type') }}</el-button>
          <el-button @click="saveForCard" type="primary">{{ t('schema_studio.save_for_card') }}</el-button>
        </template>
        <template v-else>
          <el-button type="primary" @click="saveForType">{{ t('schema_studio.save_for_type') }}</el-button>
        </template>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import OutputModelBuilder from '../setting/OutputModelBuilder.vue'
import ModelDrivenForm from '../dynamic-form/ModelDrivenForm.vue'
import { schemaToBuilder, builderToSchema, type BuilderField } from '@renderer/utils/outputModelSchemaUtils'
import { ElMessage } from 'element-plus'
import { getCardTypeSchema, updateCardTypeSchema, getCardSchema, updateCardSchema, applyCardSchemaToType, listCardTypes, updateCardType } from '@renderer/api/setting'

const { t } = useI18n()
const localeStore = useLocaleStore()

const props = defineProps<{ visible: boolean; mode: 'type' | 'card'; targetId: number; contextTitle?: string }>()
const emit = defineEmits<{ 'update:visible': [boolean]; 'saved': []; 'close': [] }>()

const headerTitle = computed(() => props.mode === 'type'
  ? t('schema_studio.type_title', { value: props.contextTitle || props.targetId })
  : t('schema_studio.card_title', { value: props.contextTitle || props.targetId }))

const builderFields = ref<BuilderField[]>([])
const relationTargets = ref<Array<{ name: string; json_schema?: any }>>([])
const previewModel = ref<any>({})
const modelName = ref<string>('')
const originalSchema = ref<any | null>(null)

const schemaObject = computed(() => {
  try {
    const base: any = builderToSchema(builderFields.value) as any

    const orig = originalSchema.value as any
    if (orig && typeof orig === 'object' && orig.properties && base && base.properties) {
      const origProps = orig.properties as Record<string, any>
      const nextProps = { ...(base.properties as Record<string, any>) }
      if (origProps.dynamic_info && Object.prototype.hasOwnProperty.call(nextProps, 'dynamic_info')) {
        nextProps.dynamic_info = origProps.dynamic_info
        base.properties = nextProps
      }
    }

    const defs: Record<string, any> = {}
    for (const f of builderFields.value) {
      if (f.kind === 'relation' && f.relation?.targetModelName) {
        const name = f.relation.targetModelName
        const found = relationTargets.value.find(m => m.name === name)
        if (found?.json_schema) defs[name] = found.json_schema
      }
    }
    if (Object.keys(defs).length) base.$defs = defs
    return base
  } catch { return null }
})
const schemaText = computed(() => {
  try { return JSON.stringify(translateSchemaForDisplay(schemaObject.value || {}), null, 2) } catch { return '' }
})


function translateSchemaForDisplay(value: any): any {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map((item) => translateSchemaForDisplay(item))
  if (value && typeof value === 'object') {
    const out: Record<string, any> = {}
    for (const [key, item] of Object.entries(value)) out[key] = translateSchemaForDisplay(item)
    return out
  }
  return value
}

async function loadSchema() {
  if (!props.visible) return
  if (!props.targetId || props.targetId <= 0) return
  try {
    if (props.mode === 'type') {
      const resp = await getCardTypeSchema(props.targetId)
      const sch = (resp?.json_schema || {})
      originalSchema.value = sch
      builderFields.value = schemaToBuilder(sch)
    } else {
      const resp = await getCardSchema(props.targetId)
      const sch = (resp?.effective_schema || resp?.json_schema || {})
      originalSchema.value = sch
      builderFields.value = schemaToBuilder(sch)
    }

    try {
      const types = await listCardTypes()
      const list = (types || []) as any[]
      relationTargets.value = list.filter(t => !!t.json_schema).map(t => ({ name: t.model_name || t.name, json_schema: t.json_schema }))
      if (props.mode === 'type') {
        const me = list.find(t => t.id === props.targetId)
        modelName.value = me?.model_name || ''
      }
    } catch {}
  } catch (e:any) {
    ElMessage.error(t('schema_studio.messages.load_failed'))
  }
}

async function saveForType() {
  try {
    if (props.mode === 'type') {
      await updateCardType(props.targetId, { model_name: modelName.value || null } as any)
    }
    await updateCardTypeSchema(props.targetId, schemaObject.value || {})
    ElMessage.success(t('schema_studio.messages.saved_to_type'))
    emit('saved')
  } catch (e:any) { ElMessage.error(t('schema_studio.messages.save_failed')) }
}

async function saveForCard() {
  try {
    await updateCardSchema(props.targetId, schemaObject.value || {})
    ElMessage.success(t('schema_studio.messages.saved_for_card'))
    emit('saved')
  } catch (e:any) { ElMessage.error(t('schema_studio.messages.save_failed')) }
}

async function restoreFollowType() {
  try {
    await updateCardSchema(props.targetId, null)
    ElMessage.success(t('schema_studio.messages.restored_follow_type'))
    await loadSchema()
    emit('saved')
  } catch (e:any) { ElMessage.error(t('schema_studio.messages.action_failed')) }
}

async function applyToType() {
  try {
    await applyCardSchemaToType(props.targetId)
    ElMessage.success(t('schema_studio.messages.applied_to_type'))
    emit('saved')
  } catch (e:any) { ElMessage.error(t('schema_studio.messages.apply_failed')) }
}

function handleKey(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    if (props.mode === 'type') saveForType()
    else saveForCard()
  }
}

watch(() => props.visible, (v) => { if (v) loadSchema() }, { immediate: false })
watch(() => props.targetId, () => { if (props.visible) loadSchema() })

onBeforeUnmount(() => { window.removeEventListener('keydown', handleKey) })

const contextTitle = computed(() => props.contextTitle || '')
</script>

<style scoped>
.studio { display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; height: 72vh; }
.left { display: flex; flex-direction: column; gap: 8px; overflow: auto; }
.right { display: grid; grid-template-rows: 1fr 1fr; gap: 8px; overflow: auto; }
.subpane { display: flex; flex-direction: column; overflow: auto; }
.pane-header { font-weight: 600; margin-bottom: 6px; }
.preview { flex: 1; overflow: auto; border: 1px solid var(--el-border-color-light); padding: 8px; border-radius: 6px; }
.footer-actions { display: flex; gap: 8px; justify-content: flex-end; width: 100%; }
.placeholder { color: var(--el-text-color-secondary); padding: 12px; }
.modelname-form { padding: 6px 0; }
:deep(.el-dialog__headerbtn) { margin-right: 6px; }
</style>
