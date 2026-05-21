<template>
  <div class="tags-editor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ t('tags_editor.title') }}</span>
          <div>
            <el-button type="primary" @click="handleRandomize">{{ t('tags_editor.random_all') }}</el-button>
            <el-button type="success" :loading="isSaving" @click="saveTags">{{ t('tags_editor.save_changes') }}</el-button>
          </div>
        </div>
      </template>
      <div class="tag-selection-container">
        <el-scrollbar>
          <div class="category-block">
            <div class="category-header">
              <h3>{{ t('tags_editor.theme_tags') }}</h3>
              <el-button @click="randomizeTheme" type="primary" plain size="small">{{ t('tags_editor.random_hint') }}</el-button>
            </div>
            <el-cascader
              :model-value="themeArray"
              @change="handleThemeChange"
              :options="themeOptions"
              :placeholder="t('tags_editor.select_novel_theme')"
              style="width: 100%"
            />
          </div>

          <div class="category-block">
            <div class="category-header">
              <h3>{{ t('tags_editor.target_audience') }}</h3>
              <el-button @click="randomizeAudience" type="primary" plain size="small">{{ t('tags_editor.random_hint') }}</el-button>
            </div>
            <el-radio-group v-model="localData.audience">
              <el-radio v-for="opt in audienceOptions" :key="opt" :value="opt" border>{{ opt }}</el-radio>
            </el-radio-group>
          </div>

          <div class="category-block">
            <div class="category-header">
              <h3>{{ t('tags_editor.narrative_person') }}</h3>
              <el-button @click="randomizePerson" type="primary" plain size="small">{{ t('tags_editor.random_hint') }}</el-button>
            </div>
            <el-radio-group v-model="localData.narrative_person">
              <el-radio v-for="opt in personOptions" :key="opt" :value="opt" border>{{ opt }}</el-radio>
            </el-radio-group>
          </div>

          <div class="category-block">
            <div class="category-header">
              <h3>{{ t('tags_editor.category_tags') }}</h3>
              <el-button @click="randomizeStoryTags" type="primary" plain size="small">{{ t('tags_editor.random_hint') }}</el-button>
            </div>
            <div class="story-tags-grid">
              <div v-for="full in categoryOptions" :key="full" class="story-tag-item">
                <el-checkbox
                  :model-value="isStoryTagSelected(full)"
                  @change="(checked) => handleStoryTagChange(checked, full)"
                >
                  {{ stripAnnotation(full) }}
                </el-checkbox>
                <el-select
                  v-if="isStoryTagSelected(full)"
                  :model-value="getStoryTagWeight(full)"
                  @change="(weight) => updateStoryTagWeight(full, weight as WeightLevel)"
                  size="small"
                  class="weight-input"
                  :placeholder="t('tags_editor.weight_placeholder')"
                >
                  <el-option v-for="w in WEIGHT_LEVELS" :key="w" :label="getWeightLabel(w)" :value="w" />
                </el-select>
              </div>
            </div>
          </div>

          <div class="category-block">
            <div class="category-header">
              <h3>{{ t('tags_editor.relationships') }}</h3>
              <el-button @click="randomizeRelationship" type="primary" plain size="small">{{ t('tags_editor.random_hint') }}</el-button>
            </div>
                          <el-radio-group v-model="localData.affection">
                <el-radio v-for="tag in relationshipOptions" :key="tag" :value="tag" border>{{ tag }}</el-radio>
              </el-radio-group>
          </div>
        </el-scrollbar>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElCard, ElButton } from 'element-plus'
import type { components } from '@renderer/types/generated'
import { useCardStore } from '@renderer/stores/useCardStore'
import { ElMessage } from 'element-plus'
import {
  ElCheckbox,
  ElRadio,
  ElRadioGroup,
  ElCascader,
  ElScrollbar,
  ElSelect,
  ElOption
} from 'element-plus'
import { onMounted } from 'vue'
import { listKnowledge } from '@renderer/api/setting'
// Define types from generated schemas
type CardRead = components['schemas']['CardRead']
type Tags = components['schemas']['Tags']
type WeightLevel = string
const legacyText = (...codes: number[]) => String.fromCharCode(...codes)
const LEGACY_WEIGHT_LOW = legacyText(20302, 26435, 37325)
const LEGACY_WEIGHT_MEDIUM = legacyText(20013, 26435, 37325)
const LEGACY_WEIGHT_HIGH = legacyText(39640, 26435, 37325)
const LEGACY_SECTION_THEME = legacyText(20027, 39064, 26631, 31614)
const LEGACY_SECTION_AUDIENCE = legacyText(30446, 26631, 32676, 20307)
const LEGACY_SECTION_PERSON = legacyText(20889, 20316, 20154, 31216)
const LEGACY_SECTION_CATEGORY = legacyText(31867, 21035, 26631, 31614)
const LEGACY_SECTION_AFFECTION = legacyText(24773, 24863, 20851, 31995)
const WEIGHT_LEVELS: WeightLevel[] = [LEGACY_WEIGHT_LOW, LEGACY_WEIGHT_MEDIUM, LEGACY_WEIGHT_HIGH]
const DEFAULT_WEIGHT: WeightLevel = LEGACY_WEIGHT_MEDIUM

const { t } = useI18n()

const props = defineProps<{
  card: CardRead
}>()

const cardStore = useCardStore()
const isSaving = ref(false)

const localData = reactive<Tags>({
  theme: '',
  audience: t('tags_editor.defaults.audience') as any,
  narrative_person: t('tags_editor.defaults.person') as any,
  story_tags: [],
  affection: ''
})
const themeOptions = ref<any[]>([])
const categoryOptions = ref<string[]>([])
const relationshipOptions = ref<string[]>([])
const audienceOptions = ref<string[]>([])
const personOptions = ref<string[]>([])

watch(
  () => props.card,
  (newCard) => {
    if (newCard && newCard.content && typeof newCard.content === 'object') {
      Object.assign(localData, newCard.content as unknown as Partial<Tags>)
    }
  },
  { deep: true, immediate: true }
)

const handleRandomize = () => {
  randomizeAll()
}

const saveTags = async () => {
  isSaving.value = true
  try {
    await cardStore.modifyCard(props.card.id, { content: localData });
    ElMessage.success(t('tags_editor.messages.saved'))
  } catch (error) {
  } finally {
    isSaving.value = false
  }
}

const themeArray = computed(() => {
  return localData.theme ? localData.theme.split('-') : []
})

function handleThemeChange(value: any) {
  if (Array.isArray(value)) {
    localData.theme = (value as string[]).join('-')
  }
}

function isStoryTagSelected(tagName: string) {
  return localData.story_tags.some(([name]) => name === tagName)
}


function getWeightLabel(weight: WeightLevel): string {
  if (weight === LEGACY_WEIGHT_LOW) return String(t('tags_editor.weights.low'))
  if (weight === LEGACY_WEIGHT_MEDIUM) return String(t('tags_editor.weights.medium'))
  if (weight === LEGACY_WEIGHT_HIGH) return String(t('tags_editor.weights.high'))
  return weight
}

function getStoryTagWeight(tagName: string): WeightLevel {
  const tag = localData.story_tags.find(([name]) => name === tagName)
  return (tag ? (tag[1] as WeightLevel) : DEFAULT_WEIGHT)
}

function handleStoryTagChange(checked: any, tagName: string) {
  const index = localData.story_tags.findIndex(([name]) => name === tagName)
  if (checked as boolean) {
    if (index === -1) {
      localData.story_tags.push([tagName, DEFAULT_WEIGHT as any])
    }
  } else {
    if (index !== -1) {
      localData.story_tags.splice(index, 1)
    }
  }
}

function updateStoryTagWeight(tagName: string, weight: WeightLevel | undefined) {
  const tag = localData.story_tags.find(([name]) => name === tagName)
  if (tag && typeof weight === 'string') {
    tag[1] = weight as any
  }
}

function randomizeAll() {
  randomizeTheme()
  randomizeAudience()
  randomizePerson()
  randomizeStoryTags()
  randomizeRelationship()
}

function randomizeTheme() {
  if (!themeOptions.value.length) return
  const mainTheme = themeOptions.value[Math.floor(Math.random() * themeOptions.value.length)]
  const subTheme = mainTheme.children[Math.floor(Math.random() * mainTheme.children.length)]
  localData.theme = `${mainTheme.value}-${subTheme.value}`
}

function randomizeStoryTags() {
  const count = Math.floor(Math.random() * 3) + 3
  const shuffled = [...categoryOptions.value].sort(() => 0.5 - Math.random())
  localData.story_tags = shuffled.slice(0, count).map(tag => {
    const weight = WEIGHT_LEVELS[Math.floor(Math.random() * WEIGHT_LEVELS.length)]
    return [tag, weight as any]
  })
}

function randomizeRelationship() {
  if (!relationshipOptions.value.length) return
  localData.affection = relationshipOptions.value[Math.floor(Math.random() * relationshipOptions.value.length)]
}

function randomizeAudience() {
  if (!audienceOptions.value.length) return
  localData.audience = audienceOptions.value[Math.floor(Math.random() * audienceOptions.value.length)] as any
}

function randomizePerson() {
  if (!personOptions.value.length) return
  localData.narrative_person = personOptions.value[Math.floor(Math.random() * personOptions.value.length)] as any
}

function stripAnnotation(label: string): string {
  return label.replace(/\s*[（(].*[）)]\s*$/, '')
}

function normalizeSectionTitle(value: string): string {
  return stripAnnotation(value)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(new RegExp(String.fromCharCode(273), 'g'), 'd')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function detectSection(content: string): 'none' | 'theme' | 'audience' | 'person' | 'category' | 'affection' {
  if (content.startsWith(LEGACY_SECTION_THEME)) return 'theme'
  if (content.startsWith(LEGACY_SECTION_AUDIENCE)) return 'audience'
  if (content.startsWith(LEGACY_SECTION_PERSON)) return 'person'
  if (content.startsWith(LEGACY_SECTION_CATEGORY)) return 'category'
  if (content.startsWith(LEGACY_SECTION_AFFECTION)) return 'affection'

  const normalized = normalizeSectionTitle(content)
  if (['chu de', 'theme', 'theme tags'].includes(normalized)) return 'theme'
  if (['doc gia muc tieu', 'audience', 'target audience'].includes(normalized)) return 'audience'
  if (['ngoi ke', 'nguoi ke', 'person', 'narrative person'].includes(normalized)) return 'person'
  if (['nhom tag', 'the loai', 'the the loai', 'category', 'category tags'].includes(normalized)) return 'category'
  if (['quan he tinh cam', 'quan he cam xuc', 'affection', 'relationships', 'emotional relationship'].includes(normalized)) return 'affection'
  return 'none'
}

function parseKnowledge(text: string) {
  const rawLines = (text || '').split(/\r?\n/)
  const lines: string[] = []
  for (const line of rawLines) {
    const normalizedLine = line.replace(/\t/g, '    ')
    if (!normalizedLine.trim().length) continue
    if (normalizedLine.trim() === '```') continue
    lines.push(normalizedLine)
  }
  type Section = 'none' | 'theme' | 'audience' | 'person' | 'category' | 'affection'
  let section: Section = 'none'
  const themes: Record<string, string[]> = {}
  let currentTheme: string | null = null
  const categories: string[] = []
  const relationships: string[] = []
  const audiences: string[] = []
  const persons: string[] = []

  for (const raw of lines) {
    const m = raw.match(/^(\s*)-\s*(.+)$/)
    if (!m) continue
    const indent = m[1].length
    const content = m[2].trim()
    const detected = indent <= 2 ? detectSection(content) : 'none'

    if (detected !== 'none') {
      section = detected
      if (section === 'theme') currentTheme = null
      continue
    }

    if (section === 'theme') {
      const ROOT_INDENT_MAX = 2
      if (indent <= ROOT_INDENT_MAX || !currentTheme) {
        const name = stripAnnotation(content)
        if (!themes[name]) themes[name] = []
        currentTheme = name
      } else {
        const sub = stripAnnotation(content)
        if (!currentTheme) {
          themes[sub] = []
          currentTheme = sub
        } else {
          themes[currentTheme].push(sub)
        }
      }
      continue
    }

    if (section === 'audience') {
      const name = stripAnnotation(content)
      if (name) audiences.push(name)
      continue
    }
    if (section === 'person') {
      const name = stripAnnotation(content)
      if (name) persons.push(name)
      continue
    }
    if (section === 'category') {
      categories.push(content)
      continue
    }
    if (section === 'affection') {
      const name = stripAnnotation(content)
      if (name) relationships.push(name)
      continue
    }
  }

  themeOptions.value = Object.keys(themes).map(k => ({
    value: k,
    label: k,
    children: (themes[k].length ? themes[k] : [k]).map(s => ({ value: s, label: s }))
  }))
  categoryOptions.value = categories
  relationshipOptions.value = relationships
  audienceOptions.value = audiences.length ? audiences : [t('tags_editor.defaults.audience'), t('tags_editor.defaults.male'), t('tags_editor.defaults.female')]
  personOptions.value = persons.length ? persons : [t('tags_editor.defaults.first_person'), t('tags_editor.defaults.third_person')]
}

onMounted(async () => {
  try {
    const list = await listKnowledge()
    const kb = (list || []).find(k => k && (k.key === 'work_tags' || k.name === t('tags_editor.title_plain')))
    if (kb && kb.content) parseKnowledge(kb.content)
  } catch {}
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tag-selection-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.category-block {
  margin-bottom: 24px;
}
.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.category-block h3 {
  margin-bottom: 0;
  font-size: 1.1em;
  font-weight: 600;
  border-left: 4px solid var(--el-color-primary);
  padding-left: 8px;
  color: var(--text-color-primary);
}

.story-tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.story-tag-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weight-input {
  width: 70px;
}

.el-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.el-radio.is-bordered {
  margin: 0;
}
</style>
