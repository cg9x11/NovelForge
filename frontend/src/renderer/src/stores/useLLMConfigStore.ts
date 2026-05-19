import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { i18n } from '@renderer/i18n'
import { listLLMConfigs, type LLMConfigRead } from '@renderer/api/setting'
const t = i18n.global.t

export const useLLMConfigStore = defineStore('llmConfig', () => {
  // State
  const llmConfigs = ref<LLMConfigRead[]>([])
  const isLoading = ref(false)

  // Actions
  async function fetchLLMConfigs() {
    isLoading.value = true
    try {
      const list = await listLLMConfigs()
      llmConfigs.value = list || []
    } catch (error) {
      console.error('获取LLM配置列表失败:', error)
      ElMessage.error(t('llm_config_store.fetch_failed'))
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    llmConfigs,
    isLoading,
    fetchLLMConfigs
  }
})
