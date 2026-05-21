<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="500">
    <el-form :model="form" ref="formRef" :rules="rules" label-width="80px" @submit.prevent="handleConfirm">
      <el-form-item :label="t('project_dialog.project_name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('project_dialog.project_description')" prop="description">
        <el-input v-model="form.description" type="textarea" />
      </el-form-item>
      <el-form-item v-if="!isEditMode" :label="t('project_dialog.project_template')">
        <el-select
          v-model="selectedTemplate"
          :placeholder="t('project_dialog.select_template_optional')"
          filterable
          clearable
          :loading="loadingTemplates"
          style="width:100%"
        >
          <el-option :label="t('project_dialog.blank_project')" :value="null" />
          <el-option v-for="tpl in projectTemplates" :key="tpl.template" :label="tr(tpl.workflow_name)" :value="tpl.template" />
        </el-select>
      </el-form-item>
      <button type="submit" style="display:none"></button>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleConfirm">{{ t('common.confirm') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { components } from '@renderer/types/generated'
import { getProjectTemplates } from '@renderer/api/workflows'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'

type Project = components['schemas']['ProjectRead']
type ProjectCreate = components['schemas']['ProjectCreate']
type ProjectUpdate = components['schemas']['ProjectUpdate']

interface ProjectTemplate {
  workflow_id: number
  workflow_name: string
  template: string | null
  description?: string
}

const { t } = useI18n()
const localeStore = useLocaleStore()
const tr = (value?: string | null) => String(value || '')

const visible = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<ProjectCreate | ProjectUpdate>({
  name: '',
  description: '',
})
const editingProject = ref<Project | null>(null)

const selectedTemplate = ref<string | null>(null)
const projectTemplates = ref<ProjectTemplate[]>([])
const loadingTemplates = ref(false)

const isEditMode = computed(() => !!editingProject.value)
const dialogTitle = computed(() =>
  isEditMode.value ? t('project_dialog.edit_title') : t('project_dialog.create_title')
)

const rules = reactive<FormRules>({
  name: [{ required: true, message: t('project_dialog.enter_project_name'), trigger: 'blur' }],
})

const emit = defineEmits(['create', 'update'])

async function loadProjectTemplates() {
  try {
    loadingTemplates.value = true
    const response = await getProjectTemplates()
    projectTemplates.value = response.templates || []
    if (projectTemplates.value.length > 0) {
      selectedTemplate.value = projectTemplates.value[0].template
    }
  } catch (error) {
    console.error('load project templates failed:', error)
    ElMessage.error(t('project_dialog.load_templates_failed'))
  } finally {
    loadingTemplates.value = false
  }
}

function open(project: Project | null = null) {
  visible.value = true
  editingProject.value = project

  nextTick(() => {
    formRef.value?.resetFields()
    if (project) {
      form.name = project.name
      form.description = project.description || ''
    } else {
      form.name = ''
      form.description = ''
      selectedTemplate.value = null
      loadProjectTemplates()
    }
  })
}

function handleConfirm() {
  formRef.value?.validate(valid => {
    if (valid) {
      if (isEditMode.value && editingProject.value) {
        emit('update', editingProject.value.id, { ...form })
      } else {
        const payload: any = { ...form }
        payload.template = selectedTemplate.value
        emit('create', payload)
      }
      visible.value = false
    } else {
      ElMessage.error(t('project_dialog.fill_required_fields'))
    }
  })
}

defineExpose({ open })
</script>

<style scoped>
.mode-switch { margin-bottom: 8px; }
.selector-block { width: 100%; }
</style>
