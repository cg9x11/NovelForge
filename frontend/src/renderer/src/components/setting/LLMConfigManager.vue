<template>
  <div class="llm-config-manager">
    <div class="header">
      <h4>{{ t('llm_config.manager_title') }}</h4>
      <el-button type="primary" size="small" @click="openEditDialog()">{{ t('llm_config.add_config') }}</el-button>
    </div>

    <el-table :data="llmConfigs" style="width: 100%" size="small">
      <el-table-column prop="display_name" :label="t('llm_config.display_name')" width="150" />
      <el-table-column prop="provider" :label="t('llm_config.provider')" width="120" />
      <el-table-column prop="model_name" :label="t('llm_config.model_name')" width="200" />
      <el-table-column label="API Base" width="240">
        <template #default="{ row }">
          <span v-if="row.provider === 'openai_compatible'">{{ row.api_base }}</span>
          <span v-else style="color: #909399; font-style: italic;">{{ t('llm_config.default_provider', { provider: row.provider }) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="token_limit" :label="t('llm_config.token_limit')" width="90" />
      <el-table-column prop="call_limit" :label="t('llm_config.call_limit')" width="90" />
      <el-table-column width="200">
        <template #header>
          <span>
            {{ t('llm_config.used_header') }}
            <el-tooltip placement="top" effect="dark">
              <template #content>
                <div v-for="(line, index) in tokenHintLines" :key="index">
                  <span v-if="line">{{ line }}</span>
                  <br />
                </div>
              </template>
              <el-icon style="margin-left:4px; cursor: help;"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <template #default="{ row }">
          {{ formatNumber((row as any).used_tokens_input || 0) }} / {{ formatNumber((row as any).used_tokens_output || 0) }} / {{ formatNumber((row as any).used_calls || 0) }}
        </template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="260">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">{{ t('common.edit') }}</el-button>
          <el-button size="small" type="primary" @click="handleCopy(row)" plain>{{ t('common.copy') }}</el-button>
          <el-button size="small" type="danger" @click="deleteConfig(row.id)">{{ t('common.delete') }}</el-button>
          <el-button size="small" type="warning" @click="handleReset(row)" plain>{{ t('common.reset') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editDialogVisible" :title="editConfig ? t('llm_config.edit_title') : t('llm_config.add_title')" width="500px">
      <LLMConfigForm
        v-if="editDialogVisible"
        :initial-data="editConfig"
        @save="handleSave"
        @cancel="editDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import LLMConfigForm from './LLMConfigForm.vue'
import type { components } from '@renderer/types/generated'
import { listLLMConfigs, createLLMConfig, updateLLMConfig, deleteLLMConfig, resetLLMUsage, copyLLMConfig } from '@renderer/api/setting'

type LLMConfig = components['schemas']['LLMConfigRead']

const llmConfigs = ref<LLMConfig[]>([])
const editDialogVisible = ref(false)
const editConfig = ref<LLMConfig | null>(null)
const { t, tm } = useI18n()

const tokenHintLines = computed(() => {
  const lines = tm('llm_config.token_hint_lines')
  return Array.isArray(lines) ? (lines as string[]) : []
})

function formatNumber(num: number): string {
  if (num >= 1000000) {
    const millions = num / 1000000
    const trimmed = parseFloat(millions.toFixed(3)).toString()
    return t('llm_config.number_million', { value: trimmed })
  }
  if (num >= 10000) {
    const tenThousands = num / 10000
    const trimmed = parseFloat(tenThousands.toFixed(3)).toString()
    return t('llm_config.number_ten_thousand', { value: trimmed })
  }
  return num.toString()
}

async function loadLLMConfigs() {
  try {
    llmConfigs.value = await listLLMConfigs()
  } catch (error) {
    console.error('Failed to load LLM configs:', error)
    ElMessage.error(t('llm_config.messages.load_failed'))
  }
}

function openEditDialog(config?: LLMConfig) {
  editConfig.value = config ?? null
  editDialogVisible.value = true
}

async function handleSave(data: any) {
  try {
    if (data.id) {
      await updateLLMConfig(data.id, data)
      ElMessage.success(t('llm_config.messages.update_success'))
    } else {
      await createLLMConfig(data)
      ElMessage.success(t('llm_config.messages.create_success'))
    }
    editDialogVisible.value = false
    await loadLLMConfigs()
  } catch {
    ElMessage.error(t('llm_config.messages.save_failed'))
  }
}

async function deleteConfig(id: number) {
  try {
    await ElMessageBox.confirm(t('llm_config.messages.delete_confirm'), t('llm_config.messages.delete_title'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await deleteLLMConfig(id)
    ElMessage.success(t('llm_config.messages.delete_success'))
    await loadLLMConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('llm_config.messages.delete_failed'))
    }
  }
}

async function handleReset(row: LLMConfig) {
  try {
    await ElMessageBox.confirm(t('llm_config.messages.reset_confirm'), t('llm_config.messages.reset_title'), {
      type: 'warning',
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel')
    })
  } catch {
    return
  }

  try {
    await resetLLMUsage(row.id)
    ElMessage.success(t('llm_config.messages.reset_success'))
    await loadLLMConfigs()
  } catch {
    ElMessage.error(t('llm_config.messages.reset_failed'))
  }
}

async function handleCopy(row: LLMConfig) {
  try {
    await copyLLMConfig(row.id)
    ElMessage.success(t('llm_config.messages.copy_success'))
    await loadLLMConfigs()
  } catch (error) {
    console.error(t('llm_config.messages.copy_failed_log'), error)
    ElMessage.error(t('llm_config.messages.copy_failed'))
  }
}

defineExpose({ refresh: loadLLMConfigs })
onMounted(loadLLMConfigs)
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
</style>
