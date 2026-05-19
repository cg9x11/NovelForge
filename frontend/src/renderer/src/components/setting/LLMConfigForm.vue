<template>
  <el-form :model="form" ref="formRef" :rules="rules" label-width="140px" autocomplete="off">
    <div style="height: 0; overflow: hidden; position: absolute; opacity: 0;">
      <input type="text" autocomplete="username" tabindex="-1">
      <input type="password" autocomplete="new-password" tabindex="-1">
    </div>

    <el-form-item :label="t('llm_form.provider')" prop="provider">
      <el-select v-model="form.provider" :placeholder="t('llm_form.select_provider')">
        <el-option :label="t('llm_form.provider_openai_compatible')" value="openai_compatible" />
        <el-option label="OpenAI" value="openai" />
        <el-option label="Google" value="google" />
        <el-option label="Anthropic" value="anthropic" />
      </el-select>
    </el-form-item>

    <el-form-item :label="t('llm_form.display_name')" prop="display_name">
      <el-input v-model="form.display_name" :placeholder="t('llm_form.display_name_placeholder')" />
    </el-form-item>

    <el-form-item label="API Base" prop="api_base">
      <el-input
        v-model="form.api_base"
        :disabled="!isOpenAIProvider"
        :input-props="{ autocomplete: 'off', name: 'api_base_no_fill' }"
        :placeholder="t('llm_form.api_base_placeholder')"
      />
    </el-form-item>

    <el-form-item label="API Key" prop="api_key">
      <el-input
        v-model="form.api_key"
        type="password"
        :input-props="{ autocomplete: 'new-password', name: 'api_key_no_fill' }"
        :placeholder="t('llm_form.api_key_placeholder')"
        show-password
      />
    </el-form-item>

    <el-form-item :label="t('llm_form.model_name')" prop="model_name">
      <div style="display: flex; width: 100%; gap: 10px; align-items: center;">
        <el-autocomplete
          v-model="form.model_name"
          :fetch-suggestions="querySearch"
          :placeholder="t('llm_form.model_name_placeholder')"
          style="flex: 1; width: 100%;"
          clearable
        />
        <el-button
          :loading="loadingModels"
          :icon="Refresh"
          :title="t('llm_form.fetch_models_title')"
          @click="handleFetchModels"
        >
          {{ t('llm_form.fetch') }}
        </el-button>
      </div>
    </el-form-item>

    <el-form-item v-if="isOpenAIProvider" :label="t('llm_form.transport_and_compat')">
      <div class="transport-settings">
        <div class="transport-summary">
          <div class="transport-copy">
            <div class="transport-title">{{ t('llm_form.transport_title') }}</div>
            <div class="transport-desc">{{ t('llm_form.transport_desc') }}</div>
          </div>
          <el-button text type="primary" @click="showAdvancedTransport = !showAdvancedTransport">
            {{ showAdvancedTransport ? t('llm_form.collapse_settings') : t('llm_form.compat_settings') }}
          </el-button>
        </div>

        <div v-if="showAdvancedTransport" class="transport-panel">
          <el-form-item :label="t('llm_form.protocol_mode')" label-width="96px" class="inline-item">
            <el-select v-model="form.api_protocol">
              <el-option :label="t('llm_form.chat_mode')" value="chat_completions" />
              <el-option :label="t('llm_form.responses_mode')" value="responses" />
            </el-select>
          </el-form-item>

          <div class="transport-rare-toggle">
            <span class="rare-toggle-text">{{ t('llm_form.rare_fields_hint') }}</span>
            <el-button text @click="showRareTransportFields = !showRareTransportFields">
              {{ showRareTransportFields ? t('llm_form.hide_fields') : t('llm_form.more_fields') }}
            </el-button>
          </div>

          <div v-if="showRareTransportFields" class="rare-transport-grid">
            <el-form-item :label="t('llm_form.custom_request_path')" label-width="96px" class="inline-item">
              <el-input
                v-model="form.custom_request_path"
                :placeholder="t('llm_form.custom_request_path_placeholder')"
                :disabled="!isOpenAIProvider"
              />
            </el-form-item>

            <el-form-item :label="t('llm_form.models_path')" label-width="96px" class="inline-item">
              <el-input
                v-model="form.models_path"
                :placeholder="t('llm_form.models_path_placeholder')"
                :disabled="!isOpenAIProvider"
              />
            </el-form-item>

            <el-form-item label="User-Agent" label-width="96px" class="inline-item">
              <el-input
                v-model="form.user_agent"
                :placeholder="t('llm_form.user_agent_placeholder')"
                :disabled="!isOpenAIProvider"
              />
            </el-form-item>
          </div>
        </div>
      </div>
    </el-form-item>

    <el-form-item :label="t('llm_form.token_limit')" prop="token_limit">
      <el-input-number v-model="form.token_limit" :min="-1" :step="1000" controls-position="right" style="width: 100%" />
      <span style="margin-left: 8px; color: #888">{{ t('llm_form.unlimited_hint') }}</span>
    </el-form-item>

    <el-form-item :label="t('llm_form.call_limit')" prop="call_limit">
      <el-input-number v-model="form.call_limit" :min="-1" :step="100" controls-position="right" style="width: 100%" />
      <span style="margin-left: 8px; color: #888">{{ t('llm_form.unlimited_hint') }}</span>
    </el-form-item>

    <el-form-item>
      <el-button @click="handleCancel">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.save') }}</el-button>
      <el-button @click="handleTest">{{ t('llm_form.test_connection') }}</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { components } from '@renderer/types/generated'
import { getLLMModels, testLLMConnection } from '@renderer/api/setting'

type LLMConfigRead = components['schemas']['LLMConfigRead']
type Provider = 'openai' | 'openai_compatible' | 'google' | 'anthropic'
type LLMApiProtocol = 'chat_completions' | 'responses'

const props = defineProps<{ initialData?: LLMConfigRead | null }>()
const emit = defineEmits<{ save: [payload: any], cancel: [] }>()
const { t } = useI18n()

const formRef = ref<FormInstance>()
const loadingModels = ref(false)
const fetchedModels = ref<string[]>([])
const showAdvancedTransport = ref(false)
const showRareTransportFields = ref(false)

const form = reactive({
  id: null as number | null,
  provider: 'openai_compatible' as Provider,
  display_name: '',
  model_name: '',
  api_base: '',
  api_key: '',
  api_protocol: 'chat_completions' as LLMApiProtocol,
  custom_request_path: '',
  models_path: '',
  user_agent: '',
  token_limit: -1,
  call_limit: -1,
})

const isOpenAIProvider = computed(() => form.provider === 'openai' || form.provider === 'openai_compatible')

const querySearch = (queryString: string, cb: any) => {
  const results = queryString
    ? fetchedModels.value.filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
    : fetchedModels.value
  cb(results.map((value) => ({ value })))
}

const rules = computed<FormRules>(() => ({
  provider: [{ required: true, message: t('llm_form.validation.select_provider'), trigger: 'change' }],
  model_name: [{ required: true, message: t('llm_form.validation.enter_model_name'), trigger: 'blur' }],
  api_key: [{ required: true, message: t('llm_form.validation.enter_api_key'), trigger: 'blur' }],
  token_limit: [{ required: true, message: t('llm_form.validation.enter_token_limit'), trigger: 'blur' }],
  call_limit: [{ required: true, message: t('llm_form.validation.enter_call_limit'), trigger: 'blur' }],
}))

watch(
  () => form.provider,
  (provider) => {
    if (!['openai', 'openai_compatible'].includes(provider)) {
      form.api_protocol = 'chat_completions'
      form.custom_request_path = ''
      form.models_path = ''
      form.user_agent = ''
      showAdvancedTransport.value = false
      showRareTransportFields.value = false
    }
  },
)

watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      form.id = newData.id
      form.provider = newData.provider as Provider
      form.display_name = newData.display_name || ''
      form.model_name = newData.model_name
      form.api_base = newData.api_base || ''
      form.api_key = newData.api_key || ''
      form.api_protocol = (((newData as any).api_protocol || 'chat_completions') === 'responses' ? 'responses' : 'chat_completions') as LLMApiProtocol
      form.custom_request_path = (newData as any).custom_request_path || ''
      form.models_path = (newData as any).models_path || ''
      form.user_agent = (newData as any).user_agent || ''
      form.token_limit = (newData as any).token_limit ?? -1
      form.call_limit = (newData as any).call_limit ?? -1
      showAdvancedTransport.value = form.api_protocol !== 'chat_completions' || !!form.custom_request_path || !!form.models_path || !!form.user_agent
      showRareTransportFields.value = !!form.custom_request_path || !!form.models_path || !!form.user_agent
      return
    }

    form.id = null
    form.provider = 'openai_compatible'
    form.display_name = ''
    form.model_name = ''
    form.api_base = ''
    form.api_key = ''
    form.api_protocol = 'chat_completions'
    form.custom_request_path = ''
    form.models_path = ''
    form.user_agent = ''
    form.token_limit = -1
    form.call_limit = -1
    showAdvancedTransport.value = false
    showRareTransportFields.value = false
  },
  { immediate: true },
)

function buildTransportPayload() {
  return {
    api_protocol: form.api_protocol || 'chat_completions',
    custom_request_path: form.custom_request_path.trim() || undefined,
    models_path: form.models_path.trim() || undefined,
    user_agent: form.user_agent.trim() || undefined,
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    ElMessage.warning(t('llm_form.messages.invalid_inputs'))
    return
  }

  emit('save', {
    ...form,
    ...buildTransportPayload(),
    api_base: form.api_base.trim() || undefined,
  })
}

async function handleFetchModels() {
  if (!form.api_key) {
    ElMessage.warning(t('llm_form.messages.enter_api_key_first'))
    return
  }

  loadingModels.value = true
  fetchedModels.value = []
  try {
    const models = await getLLMModels({
      provider: form.provider,
      api_base: form.api_base.trim() || undefined,
      api_key: form.api_key,
      ...buildTransportPayload(),
    } as any)
    fetchedModels.value = models
    if (models.length > 0) {
      ElMessage.success(t('llm_form.messages.fetch_models_success', { count: models.length }))
    } else {
      ElMessage.info(t('llm_form.messages.fetch_models_empty'))
    }
  } catch (e: any) {
    ElMessage.error(t('llm_form.messages.fetch_models_failed', { reason: e?.message || e }))
  } finally {
    loadingModels.value = false
  }
}

function handleCancel() {
  emit('cancel')
}

async function handleTest() {
  try {
    await testLLMConnection({
      provider: form.provider,
      model_name: form.model_name,
      api_base: form.api_base.trim() || undefined,
      api_key: form.api_key,
      ...buildTransportPayload(),
    } as any)
    ElMessage.success(t('llm_form.messages.test_success'))
  } catch (e: any) {
    ElMessage.error(t('llm_form.messages.test_failed', { reason: e?.message || e }))
  }
}
</script>

<style scoped>
.transport-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.transport-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
}

.transport-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.transport-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
}

.transport-desc {
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
}

.transport-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  background: var(--el-bg-color-page);
}

.transport-rare-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 0 0;
}

.rare-toggle-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.rare-transport-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
}

.inline-item {
  margin-bottom: 0;
}

.inline-item :deep(.el-form-item__content) {
  min-width: 0;
}

.inline-item :deep(.el-select),
.inline-item :deep(.el-input) {
  width: 100%;
}
</style>
