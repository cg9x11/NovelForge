<template>
  <div class="node-library">
    <div class="library-header">
      <h3>{{ t('node_library.title') }}</h3>
      <el-input v-model="searchQuery" :placeholder="t('node_library.searchPlaceholder')" clearable :prefix-icon="Search" size="small" />
    </div>

    <div class="library-content" v-loading="loading">
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
                  <div class="node-name">{{ node.label }}</div>
                  <div class="node-desc">{{ node.description || t('node_library.noDescription') }}</div>
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

const emit = defineEmits(['add-node'])
const { t } = useI18n()
const searchQuery = ref('')
const activeCategories = ref(['logic', 'novel', 'card', 'example'])
const nodeTypes = ref([])
const loading = ref(false)

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
    const matchedNodes = nodes.filter(n => n.label.toLowerCase().includes(query) || n.description.toLowerCase().includes(query) || n.type.toLowerCase().includes(query))
    if (matchedNodes.length > 0) filtered[category] = matchedNodes
  })
  return filtered
})

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
    console.error('????????:', error)
  } finally {
    loading.value = false
  }
}
onMounted(loadNodeTypes)
</script>
