<template>
  <div class="knowledge-manager">
    <div class="header">
      <h4>{{ t('knowledge_manager.title') }}</h4>
      <el-button type="primary" size="small" @click="openEditor()">{{ t('knowledge_manager.newKnowledge') }}</el-button>
    </div>

    <el-table :data="items" height="60vh" size="small" v-loading="loading">
      <el-table-column prop="key" label="Key" width="170" show-overflow-tooltip />
      <el-table-column prop="name" :label="t('knowledge_manager.columns.name')" width="90" />
      <el-table-column prop="description" :label="t('knowledge_manager.columns.description')" min-width="150" />
      <el-table-column :label="t('knowledge_manager.columns.builtIn')" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.built_in ? 'info' : 'success'">{{ row.built_in ? t('knowledge_manager.builtIn') : t('knowledge_manager.custom') }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('knowledge_manager.columns.actions')" width="180" align="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditor(row)">{{ t('common.edit') }}</el-button>
          <el-popconfirm :title="t('knowledge_manager.deleteConfirm')" @confirm="remove(row)">
            <template #reference>
              <el-button size="small" type="danger" plain :disabled="row.built_in">{{ t('common.delete') }}</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editor.visible" :title="editor.editing ? t('knowledge_manager.editKnowledge') : t('knowledge_manager.newKnowledge')" width="50%" append-to-body>
      <el-form label-position="top" :model="editor.form">
        <el-form-item label="Key"><el-input v-model="(editor.form as any).key" :disabled="editor.editing && editor.form.built_in" /></el-form-item>
        <el-form-item :label="t('knowledge_manager.form.name')"><el-input v-model="editor.form.name" :disabled="editor.editing && editor.form.built_in" /></el-form-item>
        <el-form-item :label="t('knowledge_manager.form.description')"><el-input v-model="editor.form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="t('knowledge_manager.form.content')"><el-input v-model="editor.form.content" type="textarea" :rows="14" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editor.visible=false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="save">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { listKnowledge, createKnowledge, updateKnowledge, deleteKnowledge, type Knowledge } from '@renderer/api/setting'
import { resetKnowledgeOptionCache } from '@renderer/services/knowledgeOptionResolver'

const { t } = useI18n()

const loading = ref(false)
const items = ref<Knowledge[]>([])

const editor = ref<{ visible: boolean; editing: boolean; form: Partial<Knowledge> }>({ visible: false, editing: false, form: {} })

async function fetchList() {
  loading.value = true
  try {
    items.value = await listKnowledge()
  } catch (e:any) {
    ElMessage.error(t('knowledge_manager.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

function openEditor(row?: Knowledge) {
  editor.value.visible = true
  editor.value.editing = !!row
  editor.value.form = row ? { ...row } as any : { key: '', name: '', description: '', content: '' } as any
}

async function save() {
  try {
    const f = editor.value.form
    if (!(f as any)?.key || !f?.name || !f.content) { ElMessage.warning(t('knowledge_manager.messages.fillNameAndContent')); return }
    if (editor.value.editing && f.id) {
      const saved = await updateKnowledge(f.id, { key: (f as any).key, name: f.name, description: f.description || '', content: f.content } as any)
      resetKnowledgeOptionCache()
      ElMessage.success(t('knowledge_manager.messages.updated'))
      // 局部更新
      if (saved) {
        const idx = items.value.findIndex(i => i.id === saved.id)
        if (idx >= 0) items.value[idx] = saved
      }
    } else {
      const created = await createKnowledge({ key: (f as any).key, name: f.name, description: f.description || '', content: f.content } as any)
      resetKnowledgeOptionCache()
      ElMessage.success(t('knowledge_manager.messages.created'))
      if (created) items.value.unshift(created)
    }
    editor.value.visible = false
  } catch (e:any) {
    ElMessage.error(t('knowledge_manager.messages.saveFailed'))
  }
}

async function remove(row: Knowledge) {
  try {
    await deleteKnowledge(row.id)
    resetKnowledgeOptionCache()
    ElMessage.success(t('knowledge_manager.messages.deleted'))
    items.value = items.value.filter(i => i.id !== row.id)
  } catch (e:any) {
    ElMessage.error(e?.message || t('knowledge_manager.messages.deleteFailed'))
  }
}

fetchList()
</script>

<style scoped>
.knowledge-manager { display: flex; flex-direction: column; gap: 12px; height: 100%; }
.header { display: flex; justify-content: space-between; align-items: center; }
</style> 
