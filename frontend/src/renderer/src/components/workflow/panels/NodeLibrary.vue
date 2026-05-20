<template>
  <div class="node-library">
    <div class="library-header">
      <h3>{{ t('node_library.title') }}</h3>
      <el-input v-model="searchQuery" :placeholder="t('node_library.searchPlaceholder')" clearable :prefix-icon="Search" size="small" />
    </div>

    <div class="library-content" v-loading="loading" :element-loading-text="t('common.loading')">
      <el-scrollbar>
        <el-collapse v-model="activeCategories">
          <el-collapse-item v-for="(nodes, category) in filteredNodesByCategory" :key="category" :name="category">
            <template #title>
              <div class="category-title">
                <el-icon><component :is="getCategoryIcon(category)" /></el-icon>
                <span>{{ getCategoryLabel(category) }}</span>
                <el-tag size="small" type="info">{{ nodes.length }}</el-tag>
              </div>
            </template>
            <div class="node-list">
              <div v-for="node in nodes" :key="node.type" class="node-item" @click="handleNodeClick(node)">
                <el-icon class="node-icon"><component :is="getNodeIcon(node.type)" /></el-icon>
                <div class="node-info">
                  <div class="node-name">{{ getNodeLabel(node) }}</div>
                  <div class="node-desc">{{ getNodeDescription(node) }}</div>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-scrollbar>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, Operation, Collection, DataAnalysis, MagicStick, Menu, Box, Lightning, Document } from '@element-plus/icons-vue'
import request from '@/api/request'
import { useLocaleStore } from '@/stores/useLocaleStore'

const emit = defineEmits(['add-node'])
const { t } = useI18n()
const localeStore = useLocaleStore()
const searchQuery = ref('')
const activeCategories = ref(['logic', 'novel', 'card', 'example'])
const nodeTypes = ref([])
const loading = ref(false)

const NODE_LABELS = {
  'Logic.Delay': 'Trì hoãn',
  'Logic.SelectProject': 'Chọn dự án',
  'Logic.SelectLLM': 'Chọn mô hình',
  'Logic.Wait': 'Chờ tác vụ',
  'Logic.Assert': 'Kiểm tra điều kiện',
  'Logic.Expression': 'Tính biểu thức',
  'Novel.Load': 'Tải tiểu thuyết',
  'Card.Read': 'Đọc thẻ',
  'Card.Create': 'Tạo thẻ',
  'Card.Update': 'Cập nhật thẻ',
  'Card.Delete': 'Xóa thẻ',
  'Card.Query': 'Truy vấn thẻ',
  'Card.BatchUpsert': 'Cập nhật thẻ hàng loạt',
  'Card.ReplaceFieldText': 'Thay văn bản trường',
  'Trigger.ProjectCreated': 'Kích hoạt khi tạo dự án',
  'Trigger.CardSaved': 'Kích hoạt khi lưu thẻ',
  'AI.LLM': 'Gọi LLM',
  'Prompt.Load': 'Tải prompt',
  'AI.StructuredGenerate': 'Tạo cấu trúc',
  'AI.Debate': 'Tranh luận đa tác nhân',
  'AI.BatchStructured': 'Tạo cấu trúc hàng loạt',
  'AI.SequentialStructured': 'Tạo cấu trúc tuần tự',
  'Example.Process': 'Xử lý ví dụ',
  'Example.BatchProcess': 'Xử lý hàng loạt'
}

const EN_NODE_LABELS = {
  'Logic.Delay': 'Delay',
  'Logic.SelectProject': 'Select Project',
  'Logic.SelectLLM': 'Select LLM',
  'Logic.Wait': 'Wait Task',
  'Logic.Assert': 'Assert',
  'Logic.Expression': 'Expression',
  'Novel.Load': 'Load Novel',
  'Card.Read': 'Read Card',
  'Card.Create': 'Create Card',
  'Card.Update': 'Update Card',
  'Card.Delete': 'Delete Card',
  'Card.Query': 'Query Cards',
  'Card.BatchUpsert': 'Batch Upsert Cards',
  'Card.ReplaceFieldText': 'Replace Field Text',
  'Trigger.ProjectCreated': 'Project Created Trigger',
  'Trigger.CardSaved': 'Card Saved Trigger',
  'AI.LLM': 'Call LLM',
  'Prompt.Load': 'Load Prompt',
  'AI.StructuredGenerate': 'Structured Generate',
  'AI.Debate': 'Agent Debate',
  'AI.BatchStructured': 'Batch Structured Generate',
  'AI.SequentialStructured': 'Sequential Structured Generate',
  'Example.Process': 'Example Process',
  'Example.BatchProcess': 'Batch Process'
}

const EN_NODE_DESCRIPTIONS = {
  'Logic.Delay': 'Wait for a fixed duration, then continue.',
  'Logic.SelectProject': 'Select a project by name or ID and output project info.',
  'Logic.SelectLLM': 'Select an LLM config by name or ID.',
  'Logic.Wait': 'Wait for one or more async tasks to finish.',
  'Logic.Assert': 'Validate a condition; stop workflow when it fails.',
  'Logic.Expression': 'Run a controlled Python expression and output result.',
  'Novel.Load': 'Scan a novel folder and produce chapter metadata.',
  'Card.Read': 'Read content from a card by ID, $self, or $parent.',
  'Card.Create': 'Create a new card in current project.',
  'Card.Update': 'Update content or title of an existing card.',
  'Card.Delete': 'Delete a card by ID.',
  'Card.Query': 'Find cards by query conditions.',
  'Card.BatchUpsert': 'Create or update many cards from input data.',
  'Card.ReplaceFieldText': 'Replace text in a card field.',
  'Trigger.ProjectCreated': 'Trigger workflow when a project is created.',
  'Trigger.CardSaved': 'Trigger workflow when a card is saved.',
  'AI.LLM': 'Call LLM with selected prompt and config.',
  'Prompt.Load': 'Load a prompt from the prompt library.',
  'AI.StructuredGenerate': 'Use AI to generate data matching a schema.',
  'AI.Debate': 'Let multiple agents debate and summarize a result.',
  'AI.BatchStructured': 'Generate structured data for many items.',
  'AI.SequentialStructured': 'Generate structured data sequentially with carry support.',
  'Example.Process': 'Example node for processing a list and pushing progress.',
  'Example.BatchProcess': 'Example node for batch data processing.'
}

const NODE_DESCRIPTIONS = {
  'Logic.Delay': 'Chờ một khoảng thời gian rồi tiếp tục.',
  'Logic.SelectProject': 'Chọn dự án theo tên hoặc ID và xuất thông tin dự án.',
  'Logic.SelectLLM': 'Chọn cấu hình LLM theo tên hoặc ID.',
  'Logic.Wait': 'Chờ một hoặc nhiều tác vụ bất đồng bộ hoàn tất.',
  'Logic.Assert': 'Kiểm tra điều kiện; thất bại thì dừng workflow.',
  'Logic.Expression': 'Chạy biểu thức Python có kiểm soát và xuất kết quả.',
  'Novel.Load': 'Đọc cấu trúc và nội dung tiểu thuyết từ thư mục.',
  'Card.Read': 'Đọc nội dung thẻ theo ID, $self hoặc $parent.',
  'Card.Create': 'Tạo thẻ mới trong dự án hiện tại.',
  'Card.Update': 'Cập nhật nội dung thẻ hiện có.',
  'Card.Delete': 'Xóa thẻ theo ID.',
  'Card.Query': 'Tìm danh sách thẻ theo điều kiện.',
  'Card.BatchUpsert': 'Tạo hoặc cập nhật nhiều thẻ theo dữ liệu đầu vào.',
  'Card.ReplaceFieldText': 'Thay văn bản trong một trường của thẻ.',
  'Trigger.ProjectCreated': 'Kích hoạt workflow khi dự án được tạo.',
  'Trigger.CardSaved': 'Kích hoạt workflow khi thẻ được lưu.',
  'AI.LLM': 'Gọi LLM bằng prompt và cấu hình đã chọn.',
  'Prompt.Load': 'Tải prompt từ kho prompt.',
  'AI.StructuredGenerate': 'Gọi AI để tạo dữ liệu theo schema.',
  'AI.Debate': 'Cho nhiều tác nhân tranh luận và tổng hợp kết quả.',
  'AI.BatchStructured': 'Tạo dữ liệu cấu trúc cho nhiều mục.',
  'AI.SequentialStructured': 'Tạo dữ liệu cấu trúc tuần tự, hỗ trợ carry giữa các vòng.',
  'Example.Process': 'Node ví dụ để xử lý danh sách và đẩy tiến độ.',
  'Example.BatchProcess': 'Node ví dụ để xử lý dữ liệu theo lô.'
}

const nodesByCategory = computed(() => {
  const grouped = {}
  nodeTypes.value.forEach(node => {
    if (!grouped[node.category]) grouped[node.category] = []
    grouped[node.category].push(node)
  })
  return grouped
})

const filteredNodesByCategory = computed(() => {
  if (!searchQuery.value) return nodesByCategory.value
  const query = searchQuery.value.toLowerCase()
  const filtered = {}
  Object.entries(nodesByCategory.value).forEach(([category, nodes]) => {
    const matchedNodes = nodes.filter(n =>
      getNodeLabel(n).toLowerCase().includes(query) ||
      getNodeDescription(n).toLowerCase().includes(query) ||
      n.type.toLowerCase().includes(query)
    )
    if (matchedNodes.length > 0) filtered[category] = matchedNodes
  })
  return filtered
})

const VI_NODE_LABELS = NODE_LABELS
const VI_NODE_DESCRIPTIONS = NODE_DESCRIPTIONS

const getNodeLabel = (node) => {
  if (localeStore.locale === 'vi-VN') return VI_NODE_LABELS[node.type] || node.label || node.type
  if (localeStore.locale === 'en-US') return EN_NODE_LABELS[node.type] || node.type
  return node.label || node.type
}
const getNodeDescription = (node) => {
  if (localeStore.locale === 'vi-VN') return VI_NODE_DESCRIPTIONS[node.type] || node.description || t('node_library.noDescription')
  if (localeStore.locale === 'en-US') return EN_NODE_DESCRIPTIONS[node.type] || t('node_library.noDescription')
  return node.description || t('node_library.noDescription')
}

const getCategoryIcon = (category) => ({ trigger: Lightning, logic: Operation, card: Collection, data: DataAnalysis, ai: MagicStick, novel: Document, prompt: Document, example: Box, context: Menu }[category] || Menu)
const getCategoryLabel = (category) => ({ trigger: t('node_library.categories.trigger'), logic: t('node_library.categories.logic'), card: t('node_library.categories.card'), data: t('node_library.categories.data'), ai: t('node_library.categories.ai'), novel: t('node_library.categories.novel'), prompt: t('node_library.categories.prompt'), example: t('node_library.categories.example'), context: t('node_library.categories.context') }[category] || category)
const getNodeIcon = (type) => {
  if (type.startsWith('Trigger.')) return Lightning
  if (type.startsWith('Card.')) return Collection
  if (type.startsWith('Logic.')) return Operation
  if (type.startsWith('Data.')) return DataAnalysis
  if (type.startsWith('AI.')) return MagicStick
  if (type.startsWith('Novel.')) return Document
  if (type.startsWith('Prompt.')) return Document
  return Box
}
const handleNodeClick = (node) => { emit('add-node', node.type) }
async function loadNodeTypes() {
  loading.value = true
  try {
    const response = await request.get('/nodes/types', undefined, '/api', { showLoading: false })
    nodeTypes.value = response.node_types || []
  } catch (error) {
    console.error('load node types failed:', error)
  } finally {
    loading.value = false
  }
}
onMounted(loadNodeTypes)
</script>


<style scoped>
.node-library {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.library-header {
  flex: 0 0 auto;
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.library-header h3 {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
}

.library-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.library-content :deep(.el-scrollbar) {
  height: 100%;
}

.category-title {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 6px 8px 10px;
}

.node-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  cursor: pointer;
  background: var(--el-bg-color);
}

.node-item:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}

.node-icon {
  flex: 0 0 auto;
  margin-top: 2px;
}

.node-info {
  min-width: 0;
}

.node-name {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
}

.node-desc {
  margin-top: 3px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.35;
}
</style>
