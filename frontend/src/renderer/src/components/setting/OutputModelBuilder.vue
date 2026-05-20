<template>
  <div class="schema-builder">
    <div class="toolbar">
      <el-button type="primary" @click="addField">{{ t('output_model_builder.addField') }}</el-button>
    </div>
    <el-table :data="localFields" size="small" class="field-table">
             <el-table-column :label="t('output_model_builder.columns.actions')" width="100" align="left">
        <template #default="{ $index }">
          <div class="ops-col">
            <el-button class="ops-btn" size="small" @click="moveUp($index)" :disabled="$index===0">{{ t('output_model_builder.moveUp') }}</el-button>
            <el-button class="ops-btn" size="small" @click="moveDown($index)" :disabled="$index===localFields.length-1">{{ t('output_model_builder.moveDown') }}</el-button>
            <el-button class="ops-btn" size="small" type="danger" plain @click="removeField($index)">{{ t('common.delete') }}</el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.name')" width="150">
        <template #default="{ row }">
          <el-input v-model="row.name" :placeholder="t('output_model_builder.fieldName')" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.label')" width="150">
        <template #default="{ row }">
          <el-input v-model="row.label" :placeholder="t('output_model_builder.labelPlaceholder')" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.type')" width="150">
        <template #default="{ row }">
          <el-select v-model="row.kind" @change="onKindChange(row)">
            <el-option v-for="kind in baseKinds" :key="kind" :label="kind" :value="kind" />
            <el-option label="relation(embed)" value="relation" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.array')" width="80" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.isArray" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.required')" width="80" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.required" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.aiExclude')" width="90" align="center">
        <template #default="{ row }">
          <el-switch v-model="row.aiExclude" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.description')" min-width="240">
        <template #default="{ row }">
          <el-input v-model="row.description" :placeholder="t('output_model_builder.descriptionPlaceholder')" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.example')" min-width="220">
        <template #default="{ row }">
          <el-input v-model="row.example" :placeholder="t('output_model_builder.examplePlaceholder')" />
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.tupleItems')" min-width="260">
        <template #default="{ row }">
          <div v-if="row.kind==='tuple'" class="tuple-editor">
            <div v-for="(tupleKind, i) in row.tupleItems" :key="i" class="tuple-chip">
              <el-select v-model="row.tupleItems[i]" size="small" style="width:120px">
                <el-option v-for="tk in tupleKinds" :key="tk" :label="tk" :value="tk" />
              </el-select>
              <el-button size="small" text type="danger" @click="removeTupleItem(row, i)" :disabled="(row.tupleItems?.length||0) <= 1">{{ t('output_model_builder.remove') }}</el-button>
            </div>
            <el-button size="small" text type="primary" @click="addTupleItem(row)">+ {{ t('output_model_builder.element') }}</el-button>
          </div>
          <div v-else class="rel-config muted">—</div>
        </template>
      </el-table-column>
      <el-table-column :label="t('output_model_builder.columns.relationConfig')" min-width="200">
        <template #default="{ row }">
          <div v-if="row.kind==='relation'" class="rel-config">
            <el-select v-model="row.relation.targetModelName" filterable :placeholder="t('output_model_builder.selectTargetModel')" style="width:260px">
              <el-option v-for="targetModel in targetModels" :key="targetModel.name" :label="tr(targetModel.name)" :value="targetModel.name" :disabled="isEmbedSelf(row, targetModel.name)" />
            </el-select>
          </div>
          <div v-else class="rel-config muted">—</div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { type BuilderField } from '@renderer/utils/outputModelSchemaUtils'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import { translateText } from '@renderer/locales/runtimeTranslations'

export interface OutputModelLite { name: string; json_schema?: any }

const { t } = useI18n()
const localeStore = useLocaleStore()

const props = defineProps<{ modelValue: BuilderField[]; models: OutputModelLite[]; currentModelName?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: BuilderField[]] }>()

const baseKinds: Array<BuilderField['kind']> = ['string', 'number', 'integer', 'boolean', 'tuple']
const tupleKinds: Array<NonNullable<BuilderField['tupleItems']>[number]> = ['string','number','integer','boolean']
const cjkRe = /[\u4e00-\u9fff]/

const localFields = ref<BuilderField[]>(props.modelValue?.map(cloneField) || [])
const syncingFromProps = ref(false)
watch(() => props.modelValue, async (v) => {
  syncingFromProps.value = true
  localFields.value = (v || []).map(cloneField)
  await nextTick()
  syncingFromProps.value = false
})
watch(localFields, (v) => { if (!syncingFromProps.value) emit('update:modelValue', v) }, { deep: true })

const targetModels = computed(() => props.models || [])

function tr(value?: string | null): string { return translateText(String(value || ''), localeStore.locale) }
function cleanDisplayText(value?: string | null, fallback = ''): string {
  const translated = tr(value)
  return cjkRe.test(translated) ? fallback : translated
}
function cloneField(f: BuilderField): BuilderField {
  const next = JSON.parse(JSON.stringify(f))
  if (next.label) next.label = cleanDisplayText(next.label, next.name || '')
  if (next.description) next.description = cleanDisplayText(next.description)
  return next
}
function addField() { localFields.value.push({ name: '', label: '', kind: 'string', isArray: false, required: false, aiExclude: false, relation: { targetModelName: null }, description: '', example: '', tupleItems: [] }) }
function removeField(idx: number) { localFields.value.splice(idx, 1) }
function moveUp(idx: number) { if (idx <= 0) return; const a = localFields.value; [a[idx-1], a[idx]] = [a[idx], a[idx-1]] }
function moveDown(idx: number) { const a = localFields.value; if (idx >= a.length - 1) return; [a[idx+1], a[idx]] = [a[idx], a[idx+1]] }
function onKindChange(row: BuilderField) {
  if (row.kind !== 'relation') row.relation = { targetModelName: null }
  if (row.kind === 'tuple') {
    if (!Array.isArray(row.tupleItems) || row.tupleItems.length === 0) row.tupleItems = ['string','string']
  } else {
    row.tupleItems = []
  }
}
function isEmbedSelf(row: BuilderField, targetName: string) { return row.kind === 'relation' && props.currentModelName && props.currentModelName === targetName }

function addTupleItem(row: BuilderField) {
  if (!Array.isArray(row.tupleItems)) row.tupleItems = []
  row.tupleItems.push('string')
}
function removeTupleItem(row: BuilderField, idx: number) {
  if (!Array.isArray(row.tupleItems)) return
  row.tupleItems.splice(idx, 1)
}
</script>

<style scoped>
.schema-builder { display: flex; flex-direction: column; gap: 8px; }
.toolbar { display: flex; gap: 8px; }
.field-table { width: 100%; }
.rel-config { display: flex; gap: 8px; align-items: center; }
.muted { color: var(--el-text-color-secondary); }
.tuple-editor { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.tuple-chip { display: flex; gap: 6px; align-items: center; }
.ops-col { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; width: 100%; }
.ops-col .el-button + .el-button { margin-left: 0 !important; }
.ops-btn { width: 100%; box-sizing: border-box; padding-left: 0; padding-right: 0; display: block; }
</style> 
