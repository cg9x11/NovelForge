<template>
  <div class="prompt-workshop">
    <div class="toolbar">
      <h4>{{ t('prompt_workshop.title') }}</h4>
      <el-button type="primary" size="small" @click="handleCreate">{{ t('prompt_workshop.new_prompt') }}</el-button>
    </div>
    <el-table :data="prompts" height="60vh" size="small" style="width: 100%" v-loading="loading">
      <el-table-column prop="key" :label="t('common.key')" width="190" show-overflow-tooltip />
      <el-table-column :label="t('prompt_workshop.name')" width="180">
        <template #default="{ row }">{{ tr(row.name) }}</template>
      </el-table-column>
      <el-table-column :label="t('prompt_workshop.description')">
        <template #default="{ row }">{{ tr(row.description) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="220">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
          <el-popconfirm :title="t('prompt_workshop.delete_popconfirm')" @confirm="handleDelete(row.id)" v-if="!isBuiltInPrompt(row)">
            <template #reference>
              <el-button size="small" type="danger" :disabled="isBuiltInPrompt(row)">{{ t('common.delete') }}</el-button>
            </template>
          </el-popconfirm>
          <el-button v-else size="small" type="danger" plain disabled>{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="drawerVisible" :title="dialogTitle" width="50%" append-to-body destroy-on-close class="setting-editor-dialog">
      <el-form :model="currentPrompt" label-width="90px" size="small" ref="promptForm" class="form-grid">
        <el-form-item :label="t('common.key')" prop="key">
          <el-input v-model="(currentPrompt as any).key" />
        </el-form-item>
        <el-form-item :label="t('prompt_workshop.name')" prop="name" :rules="{ required: true, message: t('prompt_workshop.validation.name_required'), trigger: 'blur' }">
          <el-input v-model="currentPrompt.name" />
        </el-form-item>
        <el-form-item :label="t('prompt_workshop.description')" prop="description">
          <el-input v-model="currentPrompt.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="t('prompt_workshop.structured_edit')">
          <el-switch v-model="useStructured" />
          <span class="hint">{{ t('prompt_workshop.structured_hint') }}</span>
        </el-form-item>

        <template v-if="useStructured">
          <el-divider content-position="left">{{ t('prompt_workshop.sections.role') }}</el-divider>
          <el-input v-model="structured.role" :placeholder="t('prompt_workshop.role_placeholder')" />

          <el-divider content-position="left">{{ t('prompt_workshop.sections.skills') }}</el-divider>
          <el-input v-model="structured.skills" type="textarea" :rows="2" :placeholder="t('prompt_workshop.skills_placeholder')" />

          <el-divider content-position="left">{{ t('prompt_workshop.sections.goals') }}</el-divider>
          <el-input v-model="structured.goals" type="textarea" :rows="4" :placeholder="t('prompt_workshop.goals_placeholder')" />

          <el-divider content-position="left">{{ t('prompt_workshop.knowledge_optional') }}</el-divider>
          <div class="knowledge-grid">
            <div class="row">
              <span class="label">{{ t('prompt_workshop.reference_mode') }}</span>
              <el-radio-group v-model="knowledgeMode" size="small">
                <el-radio-button label="id">{{ t('prompt_workshop.by_id') }}</el-radio-button>
                <el-radio-button label="name">{{ t('prompt_workshop.by_name') }}</el-radio-button>
              </el-radio-group>
              <span class="hint" style="margin-left:8px">{{ t('prompt_workshop.kb_hint') }}</span>
            </div>
            <el-select v-model="selectedKnowledgeIds" multiple filterable :placeholder="t('prompt_workshop.select_kb_placeholder')" style="width:100%">
              <el-option v-for="kb in knowledgeItems" :key="kb.id" :label="tr(kb.name)" :value="kb.id" />
            </el-select>
          </div>

          <el-divider content-position="left">{{ t('prompt_workshop.output_format_optional') }}</el-divider>
          <el-input v-model="structured.outputFormat" type="textarea" :rows="2" :placeholder="t('prompt_workshop.output_format_placeholder')" />

          <el-divider content-position="left">{{ t('prompt_workshop.preview') }}</el-divider>
          <el-input :model-value="composedTemplate" type="textarea" :rows="10" readonly />
        </template>

        <template v-else>
          <el-form-item :label="t('prompt_workshop.template')" prop="template" :rules="{ required: true, message: t('prompt_workshop.validation.template_required'), trigger: 'blur' }">
            <el-input v-model="currentPrompt.template" type="textarea" :rows="14" />
            <div class="template-hint" v-html="t('prompt_workshop.template_hint')" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <div class="drawer-footer">
          <el-button size="small" @click="drawerVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" size="small" @click="handleSave" :loading="saving">{{ t('common.save') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { listKnowledge, type Knowledge, listPrompts, createPrompt, updatePrompt, deletePrompt } from '@renderer/api/setting'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'

interface Prompt {
  id: number
  key?: string | null
  name: string
  description: string
  template: string
  built_in?: boolean
}

const { t } = useI18n()
const localeStore = useLocaleStore()
const tr = (value?: string | null) => String(value || '')
const DEFAULT_OUTPUT_FORMAT = t('prompt_workshop.default_output_format')

const prompts = ref<Prompt[]>([])
const loading = ref(false)
const drawerVisible = ref(false)
const saving = ref(false)
const currentPrompt = ref<Partial<Prompt>>({})
const promptForm = ref<FormInstance>()

const dialogTitle = computed(() => (currentPrompt.value.id ? t('prompt_workshop.edit_prompt') : t('prompt_workshop.new_prompt')))
const isBuiltInPrompt = (row: Prompt) => !!row.built_in

const useStructured = ref(false)
const structured = ref({ role: '', skills: '', goals: '', knowledge: '', outputFormat: DEFAULT_OUTPUT_FORMAT })
const knowledgeItems = ref<Knowledge[]>([])
const selectedKnowledgeIds = ref<number[]>([])
const knowledgeMode = ref<'id' | 'name'>('name')
const composedTemplate = computed(() => composeTemplate(structured.value))

function composeTemplate(s: { role: string; skills: string; goals: string; knowledge?: string; outputFormat?: string }) {
  const lines: string[] = []
  if (s.role?.trim()) lines.push(`- Role: ${s.role.trim()}`)
  if (s.skills?.trim()) lines.push(`- Skills: ${s.skills.trim()}`)
  if (s.goals?.trim()) {
    lines.push('- Goals:')
    const goalLines = s.goals.split(/\r?\n/).map(line => line.trim()).filter(Boolean)
    for (const goal of goalLines) lines.push(`    - ${goal}`)
  }
  if (selectedKnowledgeIds.value.length) {
    lines.push('\n- knowledge:')
    for (const knowledgeId of selectedKnowledgeIds.value) {
      const item = knowledgeItems.value.find(knowledge => knowledge.id === knowledgeId)
      if (!item) continue
      if (knowledgeMode.value === 'id') {
        lines.push(`    - @KB{ id=${knowledgeId} }  # ${item.name}`)
      } else {
        lines.push(`    - @KB{ name=${item.name} }`)
      }
    }
  }
  if (s.outputFormat?.trim()) lines.push(`\n- OutputFormat: ${s.outputFormat.trim()}`)
  return lines.join('\n')
}

async function fetchPrompts() {
  loading.value = true
  try {
    prompts.value = await listPrompts()
  } catch {
    ElMessage.error(t('prompt_workshop.messages.load_failed'))
  } finally {
    loading.value = false
  }
}

async function fetchKnowledgeList() {
  try {
    knowledgeItems.value = await listKnowledge()
  } catch {
    knowledgeItems.value = []
  }
}

function resetStructuredDefaults() {
  structured.value = { role: '', skills: '', goals: '', knowledge: '', outputFormat: t('prompt_workshop.default_output_format') }
  selectedKnowledgeIds.value = []
  knowledgeMode.value = 'name'
}

function handleCreate() {
  currentPrompt.value = { key: '', name: '', description: '', template: '' }
  resetStructuredDefaults()
  useStructured.value = false
  drawerVisible.value = true
}

function parseKnowledgeBlock(template: string) {
  const knowledgeMatch = /-\s*knowledge:\s*([\s\S]*?)(?:\n-\s*OutputFormat\s*[:：]|$)/i.exec(template)
  const ids: number[] = []
  let mode: 'id' | 'name' = 'name'
  if (knowledgeMatch && knowledgeMatch[1]) {
    const block = knowledgeMatch[1]
    const idReg = /@KB\{\s*id\s*=\s*(\d+)\s*\}/gi
    const nameReg = /@KB\{\s*name\s*=\s*([^}]+)\}/gi
    let match: RegExpExecArray | null
    while ((match = idReg.exec(block))) {
      const id = Number(match[1])
      if (!Number.isNaN(id)) ids.push(id)
    }
    if (!ids.length) {
      const names: string[] = []
      while ((match = nameReg.exec(block))) {
        const name = (match[1] || '').trim().replace(/^[']|[']$/g, '')
        if (name) names.push(name)
      }
      if (names.length) {
        mode = 'name'
        for (const name of names) {
          const found = knowledgeItems.value.find(knowledge => knowledge.name === name)
          if (found) ids.push(found.id)
        }
      }
    } else {
      mode = 'id'
    }
  }
  selectedKnowledgeIds.value = Array.from(new Set(ids))
  knowledgeMode.value = mode
}

async function tryParseStructured(template?: string) {
  if (!template) return resetStructuredDefaults()
  try {
    const roleMatch = /-\s*Role:\s*(.*)/i.exec(template)
    const skillsMatch = /-\s*Skills?:\s*([\s\S]*?)(?:\n-\s*Goals?:|\n-\s*knowledge:|\n-\s*OutputFormat\s*[:：]|$)/i.exec(template)
    const goalsMatch = /-\s*Goals?:\s*([\s\S]*?)(?:\n-\s*knowledge:|\n-\s*OutputFormat\s*[:：]|$)/i.exec(template)
    const outputMatch = /-\s*OutputFormat\s*[:：]\s*([\s\S]*)/i.exec(template)
    structured.value.role = roleMatch?.[1]?.trim() || ''
    structured.value.skills = (skillsMatch?.[1] || '').trim()
    structured.value.goals = (goalsMatch?.[1] || '').replace(/^\s*-\s*/gm, '').trim()
    structured.value.outputFormat = (outputMatch?.[1] || t('prompt_workshop.default_output_format')).trim()
    parseKnowledgeBlock(template)
  } catch {
    resetStructuredDefaults()
  }
}

async function handleEdit(prompt: Prompt) {
  currentPrompt.value = { ...prompt }
  await fetchKnowledgeList()
  await tryParseStructured(prompt.template)
  useStructured.value = false
  drawerVisible.value = true
}

async function handleSave() {
  if (!promptForm.value) return
  await promptForm.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload: any = { ...currentPrompt.value }
      if (useStructured.value) {
        payload.template = composeTemplate(structured.value)
      }
      if (payload.id) {
        await updatePrompt(payload.id, payload)
      } else {
        await createPrompt(payload)
      }
      ElMessage.success(t('prompt_workshop.messages.save_success'))
      drawerVisible.value = false
      fetchPrompts()
    } catch {
      ElMessage.error(t('prompt_workshop.messages.save_failed'))
    } finally {
      saving.value = false
    }
  })
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm(t('prompt_workshop.messages.delete_confirm'), t('common.warning'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    })
    await deletePrompt(id)
    ElMessage.success(t('prompt_workshop.messages.delete_success'))
    fetchPrompts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('prompt_workshop.messages.delete_failed'))
    }
  }
}

onMounted(async () => {
  await fetchKnowledgeList()
  await fetchPrompts()
})
</script>

<style scoped>
.prompt-workshop { padding: 20px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.form-grid { display: flex; flex-direction: column; gap: 8px; }
.hint { color: var(--el-text-color-secondary); margin-left: 8px; font-size: 12px; }
.template-hint { font-size: 12px; color: #909399; margin-top: 5px; }
.drawer-footer { display: flex; justify-content: flex-end; gap: 8px; }
.knowledge-grid { display: flex; flex-direction: column; gap: 8px; }
.row { display: flex; align-items: center; gap: 8px; }
.label { color: var(--el-text-color-regular); }
</style>
