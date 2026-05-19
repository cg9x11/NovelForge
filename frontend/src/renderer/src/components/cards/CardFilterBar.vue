<template>
  <div class="card-filter-bar">
    <div class="left">
      <el-input v-model="keyword" :placeholder="t('card_filter_bar.searchPlaceholder')" clearable class="search-input" @clear="emitChange" @input="emitChange">
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="selectedTypes" multiple collapse-tags :placeholder="t('card_filter_bar.typeFilter')" class="type-select" @change="emitChange">
        <el-option v-for="tOpt in typeOptions" :key="tOpt.value" :label="tOpt.label" :value="tOpt.value" />
      </el-select>
    </div>
    <div class="right">
      <el-select v-model="sortKey" class="sort-select" @change="emitChange">
        <el-option :label="t('card_filter_bar.sort.recent')" value="recent" />
        <el-option :label="t('card_filter_bar.sort.title')" value="title" />
        <el-option :label="t('card_filter_bar.sort.type')" value="type" />
      </el-select>
      <el-segmented v-model="density" :options="densityOptions" @change="emitChange" class="density-seg" />
      <el-segmented v-model="viewMode" :options="viewOptions" @change="emitChange" class="view-seg" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElInput, ElSelect, ElOption, ElSegmented, ElIcon } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import type { components } from '@renderer/types/generated'

const props = defineProps<{ cardTypes: components['schemas']['CardTypeRead'][] }>()
const emit = defineEmits<{
  (e: 'change', payload: { keyword: string; types: number[]; sortKey: 'recent'|'title'|'type'; density: string; view: string }): void
}>()

const { t } = useI18n()
const keyword = ref('')
const selectedTypes = ref<number[]>([])
const sortKey = ref<'recent'|'title'|'type'>('recent')
const density = ref<string>(t('card_filter_bar.density.comfortable'))
const viewMode = ref<string>(t('card_filter_bar.views.card'))

const densityOptions = computed(() => [t('card_filter_bar.density.comfortable'), t('card_filter_bar.density.compact')])
const viewOptions = computed(() => [t('card_filter_bar.views.card'), t('card_filter_bar.views.list')])
const typeOptions = computed(() => (props.cardTypes || []).map(tOpt => ({ label: tOpt.name, value: tOpt.id! })))

function emitChange() {
  emit('change', { keyword: keyword.value, types: selectedTypes.value, sortKey: sortKey.value, density: density.value, view: viewMode.value })
}
</script>

<style scoped>
.card-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0 16px 0;
}
.left { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; flex: 1; }
.right { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.search-input { max-width: 360px; width: 100%; }
.type-select { min-width: 220px; }
.sort-select { width: 140px; }
.density-seg, .view-seg { --el-segmented-padding: 2px; }
</style>
