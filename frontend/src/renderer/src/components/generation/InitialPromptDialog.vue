<template>
  <el-dialog
    v-model="dialogVisible"
    :title="t('initial_prompt.title')"
    width="500px"
    :close-on-click-modal="false"
  >
    <div class="dialog-content">
      <p class="hint-text">
        {{ t('initial_prompt.optional_hint') }}
      </p>
      <p class="hint-subtext">
        {{ t('initial_prompt.direct_generate_hint') }}
      </p>

      <el-checkbox v-model="useExistingContent" class="content-option">
        {{ t('initial_prompt.continue_existing') }}
      </el-checkbox>

      <el-input
        v-model="userPrompt"
        type="textarea"
        :rows="4"
        :placeholder="t('initial_prompt.placeholder')"
        maxlength="500"
        show-word-limit
        @keyup.ctrl.enter="handleStartGenerate"
      />

      <div class="example-hints">
        <span class="example-label">{{ t('initial_prompt.example') }}</span>
        <el-tag
          v-for="example in examples"
          :key="example"
          size="small"
          class="example-tag"
          @click="userPrompt = example"
        >
          {{ example }}
        </el-tag>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">
          {{ t('common.cancel') }}
        </el-button>
        <el-button @click="handleSkip">
          {{ t('initial_prompt.skip_and_generate') }}
        </el-button>
        <el-button
          type="primary"
          :disabled="!userPrompt.trim()"
          @click="handleStartGenerate"
        >
          {{ t('initial_prompt.start_generate') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

// ==================== Props & Emits ====================

const { t } = useI18n()

const props = defineProps<{
  visible: boolean
  cardTypeName?: string
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  confirm: [userPrompt: string, useExistingContent: boolean]
  cancel: []
}>()

// ==================== 状态管理 ====================

const dialogVisible = ref(false)
const userPrompt = ref('')
const useExistingContent = ref(false)

// 示例提示（根据卡片类型动态调整）
const examples = ref<string[]>([
  t('initial_prompt.examples.character_1'),
  t('initial_prompt.examples.character_2'),
  t('initial_prompt.examples.character_3')
])

// ==================== 方法 ====================

/**
 * 处理开始生成
 */
function handleStartGenerate() {
  emit('confirm', userPrompt.value.trim(), useExistingContent.value)
  dialogVisible.value = false
  userPrompt.value = ''
  useExistingContent.value = false
}

/**
 * 处理跳过
 */
function handleSkip() {
  emit('confirm', '', useExistingContent.value)
  dialogVisible.value = false
  userPrompt.value = ''
  useExistingContent.value = false
}

/**
 * 处理取消
 */
function handleCancel() {
  emit('cancel')
  dialogVisible.value = false
  userPrompt.value = ''
}

// ==================== 监听 ====================

watch(() => props.visible, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  emit('update:visible', val)
})

// 根据卡片类型调整示例
watch(() => props.cardTypeName, (typeName) => {
  if (!typeName) return

  // 可以根据不同的卡片类型提供不同的示例
  if (typeName.includes('角色') || typeName.includes('Character')) {
    examples.value = [
      t('initial_prompt.examples.character_1'),
      t('initial_prompt.examples.character_2'),
      t('initial_prompt.examples.character_3')
    ]
  } else if (typeName.includes('章节') || typeName.includes('Chapter')) {
    examples.value = [
      t('initial_prompt.examples.chapter_1'),
      t('initial_prompt.examples.chapter_2'),
      t('initial_prompt.examples.chapter_3')
    ]
  } else if (typeName.includes('大纲') || typeName.includes('Outline')) {
    examples.value = [
      t('initial_prompt.examples.outline_1'),
      t('initial_prompt.examples.outline_2'),
      t('initial_prompt.examples.outline_3')
    ]
  } else {
    examples.value = [
      t('initial_prompt.examples.generic_1'),
      t('initial_prompt.examples.generic_2'),
      t('initial_prompt.examples.generic_3')
    ]
  }
})
</script>

<style scoped>
.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hint-text {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.hint-subtext {
  margin: -8px 0 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.example-hints {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.example-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
