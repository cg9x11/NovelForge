<template>
  <div class="sectioned-form">
    <el-collapse v-model="activeNames">
      <el-collapse-item v-for="(sec, idx) in sections" :key="idx" :name="String(idx)">
        <template #title>
          <span class="sec-title">{{ tr(sec.title) }}</span>
          <span class="sec-desc" v-if="sec.description">{{ tr(sec.description) }}</span>
        </template>
        <ModelDrivenForm
          :schema="schema"
          v-model="proxy"
          :include-fields="sec.include"
          :exclude-fields="sec.exclude"
        />
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import type { JSONSchema } from '@renderer/api/schema'
import ModelDrivenForm from './ModelDrivenForm.vue'
import type { SectionConfig } from '@renderer/services/uiLayoutService'

const props = defineProps<{ schema: JSONSchema | undefined; modelValue: any; sections: SectionConfig[] }>()
const emit = defineEmits(['update:modelValue'])
const localeStore = useLocaleStore()
const tr = (value?: string) => String(value || '')

const proxy = ref<any>(props.modelValue)
watch(() => props.modelValue, v => proxy.value = v, { deep: true })
watch(proxy, v => emit('update:modelValue', v), { deep: true })

const activeNames = ref<string[]>([])

let initialized = false
watch(() => props.sections, (secs) => {
  const namesAll = secs.map((_, i) => String(i))
  if (!initialized) {
    activeNames.value = secs.map((s, i) => (!s.collapsed ? String(i) : '')).filter(Boolean) as string[]
    initialized = true
    return
  }
  const preserved = activeNames.value.filter(n => namesAll.includes(n))
  const newlyOpen = secs
    .map((s, i) => ({ i, s }))
    .filter(({ i, s }) => !s.collapsed && !preserved.includes(String(i)))
    .map(({ i }) => String(i))
  activeNames.value = [...preserved, ...newlyOpen]
}, { immediate: true })
</script>

<style scoped>
.sectioned-form { display: flex; flex-direction: column; gap: 8px; }
.sec-title { font-weight: 600; margin-right: 8px; }
.sec-desc { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
