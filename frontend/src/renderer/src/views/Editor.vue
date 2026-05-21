<template>
  <div class="editor-shell">
    <div v-if="showProjectTopbar" class="editor-topbar">
      <div class="editor-topbar__left">
        <el-button size="small" @click="emit('back-to-dashboard')">{{ t('common.back') }}</el-button>
        <span class="editor-topbar__title">{{ projectStore.currentProject?.name }}</span>
      </div>
    </div>

  <div class="editor-layout">
    <el-aside class="sidebar card-navigation-sidebar" :style="{ width: leftSidebarDisplayWidth + 'px' }" @contextmenu.prevent="onSidebarContextMenu">
      <div class="sidebar-header">
        <h3 class="sidebar-title">{{ t('editor.sidebar.title') }}</h3>

      </div>

      <div class="types-pane" :style="{ height: typesPaneHeight + 'px' }" @dragover.prevent @drop="onTypesPaneDrop">
        <div class="pane-title">{{ t('editor.sidebar.card_types') }}</div>
        <el-scrollbar class="types-scroll">
          <ul class="types-list">
            <li v-for="t in cardStore.cardTypes" :key="t.id" class="type-item" draggable="true"
                @dragstart="onTypeDragStart(t)">
              <span class="type-name">{{ trRuntime(t.name) }}</span>
            </li>
          </ul>
        </el-scrollbar>
      </div>
      <div class="inner-resizer" @mousedown="startResizingInner"></div>

      <div class="cards-pane" :style="{ height: `calc(100% - ${typesPaneHeight + innerResizerThickness}px)` }" @dragover.prevent @drop="onCardsPaneDrop">
        <div class="cards-title">
          <div class="cards-title-head">
            <div class="cards-title-text">{{ t('editor.sidebar.current_project', { name: projectStore.currentProject?.name }) }}</div>
            <div v-if="selectedCardIds.length > 0" class="cards-selection-chip">{{ t('editor.sidebar.selected_count', { count: selectedCardIds.length }) }}</div>
          </div>
          <div class="cards-title-actions">
            <el-button
              class="toolbar-action"
              :class="selectedCardIds.length > 0 ? 'toolbar-action-create-split' : 'toolbar-action-create-full'"
              size="small"
              type="primary"
              :icon="Plus"
              @click="openCreateRoot"
            >
              {{ t('editor.actions.create_card') }}
            </el-button>
            <el-button
              v-if="selectedCardIds.length > 0"
              class="toolbar-action toolbar-action-danger toolbar-action-danger-split"
              size="small"
              type="danger"
              :icon="Delete"
              @click="batchDeleteCards"
            >
              {{ t('editor.actions.delete_selected', { count: selectedCardIds.length }) }}
            </el-button>
            <el-button v-if="!isFreeProject" class="toolbar-action toolbar-action-secondary" size="small" :icon="Upload" @click="openImportFreeCards">{{ t('editor.actions.import_cards') }}</el-button>
            <el-button class="toolbar-action toolbar-action-secondary" :class="{ 'toolbar-action-secondary--solo': isFreeProject }" size="small" :icon="Download" @click="openExportDialog">{{ t('editor.actions.export_cards') }}</el-button>
          </div>
        </div>

        <div class="search-box" style="padding: 0 8px 8px;">
           <el-input
             v-model="searchQuery"
             :placeholder="t('editor.search.placeholder')"
             :prefix-icon="Search"
             clearable
             @input="handleSearch"
           />
        </div>

        <div v-if="isSearching" class="search-results-list" v-loading="searchLoading">
           <div
             v-for="card in searchResults"
             :key="card.id"
             class="search-item"
             @click="handleNodeClick({ id: card.id, title: card.title, card_type: card.card_type })"
           >
              <el-icon class="card-icon"><component :is="getIconByCardType(card.card_type)" /></el-icon>
              <span class="search-item-title">{{ card.title }}</span>
           </div>
           <el-empty v-if="!searchLoading && searchResults.length === 0" :description="t('editor.search.no_results')" :image-size="60" />
        </div>

        <template v-else>
          <el-tree
            v-if="groupedTree.length > 0"
            ref="treeRef"
            :data="groupedTree"
            node-key="id"
            :default-expanded-keys="expandedKeys"
            :expand-on-click-node="false"
            @node-click="handleNodeClick"
            @node-expand="onNodeExpand"
            @node-collapse="onNodeCollapse"
            draggable
            :allow-drop="handleAllowDrop"
            :allow-drag="handleAllowDrag"
            @node-drop="handleNodeDrop"
            class="card-tree"
          >
            <template #default="{ node, data }">
              <el-dropdown class="full-row-dropdown" trigger="contextmenu" @command="(cmd:string) => handleContextCommand(cmd, data)">
                <div
                  class="custom-tree-node full-row"
                  :class="{ 'selected': isCardSelected(data.id) }"
                  @click.stop="handleCardClick($event, data)"
                  @dragover.prevent
                  @drop="(e:any) => onExternalDropToNode(e, data)"
                  @dragenter.prevent
                >
                  <el-icon class="card-icon">
                    <component :is="getIconByCardType(data.card_type || data.__groupTypeKey || data.__groupType)" />
                  </el-icon>
                  <span class="label">{{ trRuntime(node.label || data.title) }}</span>
                  <span v-if="data.children && data.children.length > 0" class="child-count">{{ data.children.length }}</span>
                </div>
                <template #dropdown>
                  <el-dropdown-menu>
                    <template v-if="!data.__isGroup">
                      <el-dropdown-item command="create-child" :disabled="selectedCardIds.length > 1">{{ t('editor.context.create_child') }}</el-dropdown-item>
                      <el-dropdown-item command="rename" :disabled="selectedCardIds.length > 1">{{ t('common.rename') }}</el-dropdown-item>
                      <el-dropdown-item command="edit-structure" :disabled="selectedCardIds.length > 1">{{ t('editor.context.edit_structure') }}</el-dropdown-item>
                      <el-dropdown-item command="add-as-reference" :disabled="selectedCardIds.length > 1">{{ t('editor.context.add_as_reference') }}</el-dropdown-item>
                      <el-dropdown-item v-if="selectedCardIds.length > 1" command="batch-delete" divided>{{ t('editor.context.delete_selected_cards', { count: selectedCardIds.length }) }}</el-dropdown-item>
                      <el-dropdown-item v-else command="delete" divided>{{ t('editor.context.delete_card') }}</el-dropdown-item>
                    </template>
                    <template v-else>
                      <el-dropdown-item command="create-child-in-group">{{ t('editor.context.create_child') }}</el-dropdown-item>
                      <el-dropdown-item command="delete-group" divided>{{ t('editor.context.delete_group_cards') }}</el-dropdown-item>
                    </template>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-tree>
          <el-empty v-else :description="t('editor.empty.no_cards')" :image-size="80"></el-empty>
        </template>
      </div>

      <span ref="blankMenuRef" class="blank-menu-ref" :style="{ position: 'fixed', left: blankMenuX + 'px', top: blankMenuY + 'px', width: '1px', height: '1px' }"></span>
      <el-dropdown v-model:visible="blankMenuVisible" trigger="manual">
        <span></span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="openCreateRoot">{{ t('editor.actions.new_card') }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-aside>

    <div v-if="isLeftSidebarVisible" class="resizer left-resizer" @mousedown="startResizing('left')"></div>

    <el-main class="main-content">
      <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
        <el-tab-pane :label="t('editor.tabs.library')" name="market">
          <CardMarket @edit-card="handleEditCard" />
        </el-tab-pane>
        <el-tab-pane :label="t('editor.tabs.editor')" name="editor">
          <template v-if="activeCard">
            <CardEditorHost :card="activeCard" :prefetched="prefetchedContext" />
          </template>
          <el-empty v-else :description="t('editor.empty.select_card')" />
        </el-tab-pane>
        <el-tab-pane :label="t('editor.tabs.relation_graph')" name="relation-graph">
          <RelationGraphPanel :refresh-seq="relationGraphRefreshSeq" />
        </el-tab-pane>
      </el-tabs>
    </el-main>

    <div class="resizer right-resizer" @mousedown="startResizing('right')"></div>
    <el-aside class="sidebar assistant-sidebar" :style="{ width: rightSidebarWidth + 'px' }">
      <template v-if="showRightSidebarTabs">
        <el-tabs v-model="activeRightTab" type="card" class="right-tabs">
          <el-tab-pane :label="t('editor.tabs.assistant')" name="assistant">
            <AssistantPanel
              :resolved-context="assistantResolvedContext"
              :llm-config-id="assistantParams.llm_config_id as any"
              :prompt-name="t('assistant.default_prompt')"
              :temperature="assistantParams.temperature as any"
              :max_tokens="assistantParams.max_tokens as any"
              :timeout="assistantParams.timeout as any"
              :effective-schema="assistantEffectiveSchema"
              :generation-prompt-name="assistantParams.prompt_name as any"
              :current-card-title="assistantSelectionCleared ? '' : trRuntime(activeCard?.title as any)"
              :current-card-content="assistantSelectionCleared ? null : (activeCard?.content as any)"
              @refresh-context="refreshAssistantContext"
              @reset-selection="resetAssistantSelection"
              @finalize="assistantFinalize"
              @jump-to-card="handleJumpToCard"
            />
          </el-tab-pane>

          <template v-if="isChapterContent">
          <el-tab-pane :label="t('editor.tabs.entities')" name="context">
            <ContextPanel
              :project-id="projectStore.currentProject?.id"
              :prefetched="prefetchedContext"
              :volume-number="chapterVolumeNumber"
              :chapter-number="chapterChapterNumber"
              :participants="chapterParticipants"
              @update:participants="handleContextParticipantsUpdate"
              @context-updated="handleContextAssembledUpdate"
            />
          </el-tab-pane>

          <el-tab-pane :label="t('editor.tabs.extract')" name="extract">
            <ChapterToolsPanel />
          </el-tab-pane>

          <el-tab-pane :label="t('editor.tabs.outline')" name="outline">
            <OutlinePanel
              :active-card="activeCard"
              :volume-number="chapterVolumeNumber"
              :chapter-number="chapterChapterNumber"
            />
          </el-tab-pane>
          </template>

          <el-tab-pane :label="t('editor.tabs.review_history')" name="review-history">
            <ReviewHistoryPanel
              :target-card-id="reviewTargetCardIdForSidebar"
            />
          </el-tab-pane>
        </el-tabs>
      </template>

      <AssistantPanel
        v-else
        :resolved-context="assistantResolvedContext"
        :llm-config-id="assistantParams.llm_config_id as any"
        :prompt-name="t('assistant.default_prompt')"
        :temperature="assistantParams.temperature as any"
        :max_tokens="assistantParams.max_tokens as any"
        :timeout="assistantParams.timeout as any"
        :effective-schema="assistantEffectiveSchema"
        :generation-prompt-name="assistantParams.prompt_name as any"
        :current-card-title="assistantSelectionCleared ? '' : trRuntime(activeCard?.title as any)"
        :current-card-content="assistantSelectionCleared ? null : (activeCard?.content as any)"
        @refresh-context="refreshAssistantContext"
        @reset-selection="resetAssistantSelection"
        @finalize="assistantFinalize"
        @jump-to-card="handleJumpToCard"
      />
    </el-aside>
    <el-tooltip :content="isLeftSidebarVisible ? t('editor.sidebar.collapse') : t('editor.sidebar.expand')" placement="right">
      <button
        type="button"
        class="sidebar-edge-toggle"
        :class="{ 'is-collapsed': !isLeftSidebarVisible }"
        :style="{ left: `${leftSidebarToggleOffset}px` }"
        :aria-label="isLeftSidebarVisible ? t('editor.sidebar.collapse') : t('editor.sidebar.expand')"
        @click="toggleLeftSidebar"
      >
        <el-icon class="sidebar-edge-toggle__icon">
          <component :is="isLeftSidebarVisible ? ArrowLeft : ArrowRight" />
        </el-icon>
      </button>
    </el-tooltip>
  </div>
  </div>

  <el-dialog v-model="isCreateCardDialogVisible" :title="t('editor.create_dialog.title')" width="500px">
    <el-form :model="newCardForm" label-position="top">
      <el-form-item :label="t('editor.create_dialog.card_title')">
        <el-input v-model="newCardForm.title" :placeholder="t('editor.create_dialog.card_title_placeholder')"></el-input>
      </el-form-item>
      <el-form-item :label="t('editor.create_dialog.card_type')">
        <el-select v-model="newCardForm.card_type_id" :placeholder="t('editor.create_dialog.card_type_placeholder')" style="width: 100%">
          <el-option
            v-for="type in cardStore.cardTypes"
            :key="type.id"
            :label="trRuntime(type.name)"
            :value="type.id"
          ></el-option>
        </el-select>
      </el-form-item>
      <el-form-item :label="t('editor.create_dialog.parent_card')">
                <el-tree-select
           v-model="newCardForm.parent_id"
           :data="cardTree"
           :props="treeSelectProps"
           check-strictly
           :render-after-expand="false"
           :placeholder="t('editor.create_dialog.parent_card_placeholder')"
           clearable
           style="width: 100%"
         />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="isCreateCardDialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleCreateCard">{{ t('common.create') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="importDialog.visible" :title="t('editor.import_dialog.title')" width="900px" class="nf-import-dialog">
    <div style="display:flex; gap:12px; align-items:center; margin-bottom:8px; flex-wrap: wrap;">
      <el-select v-model="importDialog.sourcePid" :placeholder="t('editor.import_dialog.source_project')" style="width:220px" @change="onImportSourceChange($event as any)">
        <el-option v-for="p in importDialog.projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-input v-model="importDialog.search" :placeholder="t('editor.import_dialog.search_placeholder')" clearable style="flex:1; min-width: 200px" />
      <el-select v-model="importFilter.types" multiple collapse-tags :placeholder="t('editor.import_dialog.type_filter')" style="min-width:220px;" :max-collapse-tags="2">
        <el-option v-for="t in cardStore.cardTypes" :key="t.id" :label="t.name" :value="t.id!" />
      </el-select>
      <el-tree-select
        v-model="importDialog.parentId"
        :data="cardTree"
        :props="treeSelectProps"
        check-strictly
        :render-after-expand="false"
        :placeholder="t('editor.import_dialog.target_parent')"
        clearable
        popper-class="nf-tree-select-popper"
        style="width: 300px"
      />
    </div>
    <el-table :data="filteredImportCards" height="360px" border @selection-change="onImportSelectionChange">
      <el-table-column type="selection" width="48" />
      <el-table-column :label="t('common.title')" prop="title" min-width="220" />
      <el-table-column :label="t('common.type')" min-width="160">
        <template #default="{ row }">{{ trRuntime(row.card_type?.name) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.created_at')" min-width="160">
        <template #default="{ row }">{{ (row as any).created_at }}</template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="importDialog.visible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :disabled="!selectedImportIds.length" @click="confirmImportCards">{{ t('editor.import_dialog.import_selected') }}</el-button>
    </template>
  </el-dialog>

  <SchemaStudio v-model:visible="schemaStudio.visible" :mode="'card'" :target-id="schemaStudio.cardId" :context-title="trRuntime(schemaStudio.cardTitle)" @saved="onCardSchemaSaved" />
  <CardExportDialog
    v-model="exportDialogVisible"
    :project-id="projectStore.currentProject?.id"
    :project-name="projectStore.currentProject?.name"
    :cards="cards as any"
    :card-types="cardStore.cardTypes as any"
    :initial-card-id="selectedCardIds.length === 1 ? selectedCardIds[0] : ((activeCard as any)?.id ?? null)"
  />


</template>

<script setup lang="ts">
import { ref, onMounted, reactive, defineAsyncComponent, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLocaleStore } from '@renderer/stores/useLocaleStore'
import { storeToRefs } from 'pinia'
import { Plus, Search, Upload, Download, Delete, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { debounce } from 'lodash-es'
import {
  Box,
  CollectionTag,
  MagicStick,
  ChatLineRound,
  List,
  Connection,
  Tickets,
  Notebook,
  User,
  OfficeBuilding,
  Document,
  Folder,
} from '@element-plus/icons-vue'
import type { components } from '@renderer/types/generated'
import { useSidebarResizer } from '@renderer/composables/useSidebarResizer'
import AssistantPanel from '@renderer/components/assistants/AssistantPanel.vue'
import ContextPanel from '@renderer/components/panels/ContextPanel.vue'
import ChapterToolsPanel from '@renderer/components/panels/ChapterToolsPanel.vue'
import OutlinePanel from '@renderer/components/panels/OutlinePanel.vue'
import ReviewHistoryPanel from '@renderer/components/panels/ReviewHistoryPanel.vue'
import RelationGraphPanel from '@renderer/components/panels/RelationGraphPanel.vue'
import { useCardStore } from '@renderer/stores/useCardStore'
import { useEditorStore } from '@renderer/stores/useEditorStore'
import { useProjectStore } from '@renderer/stores/useProjectStore'
import { useAssistantStore } from '@renderer/stores/useAssistantStore'
import SchemaStudio from '@renderer/components/shared/SchemaStudio.vue'
import { getCardSchema, createCardType } from '@renderer/api/setting'
import { getProjects } from '@renderer/api/projects'
import { getCardsForProject, copyCard, getCardAIParams, searchCards } from '@renderer/api/cards'
import { DEFAULT_ASSISTANT_PROMPT_KEY, generateAIContent } from '@renderer/api/ai'
import { getCardTypeKey, isCardType } from '@renderer/utils/cardType'
import type { AssistantRef, ChapterExcerptRef, ReviewResultRef } from '@renderer/api/ai'

 // Mock components that will be created later
 const CardEditorHost = defineAsyncComponent(() => import('@renderer/components/cards/CardEditorHost.vue'));
 const CardMarket = defineAsyncComponent(() => import('@renderer/components/cards/CardMarket.vue'));
 const CardExportDialog = defineAsyncComponent(() => import('@renderer/components/cards/CardExportDialog.vue'));


 type Project = components['schemas']['ProjectRead']
 type CardRead = components['schemas']['CardRead']
 type CardCreate = components['schemas']['CardCreate']

 const importDialog = ref<{ visible: boolean; search: string; parentId: number | null; sourcePid: number | null; projects: Array<{id:number; name:string}> }>({ visible: false, search: '', parentId: null, sourcePid: null, projects: [] })
 const importSourceCards = ref<CardRead[]>([])
 const selectedImportIds = ref<number[]>([])

 const importFilter = ref<{ types: number[] }>({ types: [] })

 const filteredImportCards = computed(() => {
   const q = (importDialog.value.search || '').trim().toLowerCase()
   let list = importSourceCards.value || []
   if (importFilter.value.types.length) {
     const typeSet = new Set(importFilter.value.types)
     list = list.filter(c => c.card_type?.id && typeSet.has(c.card_type.id))
   }
   if (q) {
     list = list.filter(c => (c.title || '').toLowerCase().includes(q))
   }
   return list
 })

async function openImportFreeCards() {
  try {
    const list = await getProjects()
    const currentId = projectStore.currentProject?.id
     importDialog.value.projects = (list || []).filter(p => p.id !== currentId).map(p => ({ id: p.id!, name: p.name! }))
     importDialog.value.sourcePid = importDialog.value.projects[0]?.id ?? null
     selectedImportIds.value = []
     await onImportSourceChange(importDialog.value.sourcePid as any)
     importDialog.value.visible = true
  } catch { ElMessage.error(t('editor.messages.load_source_projects_failed')) }
 }

function openExportDialog() {
  if (!projectStore.currentProject?.id) {
    ElMessage.warning(t('editor.messages.select_project_first'))
    return
  }
  if ((cards.value || []).length === 0) {
    ElMessage.warning(t('editor.messages.no_cards_to_export'))
    return
  }
  exportDialogVisible.value = true
}

 async function onImportSourceChange(pid: number | null) {
   importSourceCards.value = []
   if (!pid) return
   try { importSourceCards.value = await getCardsForProject(pid) } catch { importSourceCards.value = [] }
 }

 function onImportSelectionChange(rows: any[]) {
   selectedImportIds.value = (rows || []).map(r => Number(r.id)).filter(n => Number.isFinite(n))
 }

 async function confirmImportCards() {
   try {
     const pid = projectStore.currentProject?.id
     if (!pid) return
     const targetParent = importDialog.value.parentId || null
     for (const id of selectedImportIds.value) {
       await copyCard(id, { target_project_id: pid, parent_id: targetParent as any })
     }
     await cardStore.fetchCards(pid)
     ElMessage.success(t('editor.messages.import_selected_success'))
     importDialog.value.visible = false
   } catch { ElMessage.error(t('editor.messages.import_failed')) }
 }

 // Props
 const props = withDefaults(defineProps<{
   initialProject: Project
   showProjectTopbar?: boolean
 }>(), {
   showProjectTopbar: true
 })
 const emit = defineEmits<{
   (e: 'back-to-dashboard'): void
 }>()

 // Store
 const cardStore = useCardStore()
 const { cardTree, activeCard, cards } = storeToRefs(cardStore)
 const editorStore = useEditorStore()
 const { expandedKeys } = storeToRefs(editorStore)
 const projectStore = useProjectStore()
 const assistantStore = useAssistantStore()
 const isFreeProject = computed(() => (projectStore.currentProject?.name || '') === '__free__')
 const showProjectTopbar = computed(() => props.showProjectTopbar && !isFreeProject.value)

 interface TreeNode { id: number | string; title: string; children?: TreeNode[]; card_type?: { name: string; key?: string; output_model_name?: string }; __isGroup?: boolean; __groupType?: string; __groupTypeKey?: string }


 function buildGroupedNodes(nodes: any[]): any[] {
  return nodes.map(n => {
    const node: TreeNode = { ...n }
    if ((n as any).__isGroup) {
      if (Array.isArray(n.children) && n.children.length > 0) {
        node.children = buildGroupedNodes(n.children as any)
      }
      return node
    }
    if (Array.isArray(n.children) && n.children.length > 0) {
      const byType: Record<string, { title: string; key: string; cards: any[] }> = {}
      n.children.forEach((c: any) => {
        const typeTitle = c.card_type?.name || t('common.unknown')
        const typeKey = getCardTypeKey(c.card_type) || typeTitle
        if (!byType[typeKey]) byType[typeKey] = { title: typeTitle, key: typeKey, cards: [] }
        byType[typeKey].cards.push(c)
      })
      const groups = Object.values(byType)
        const grouped: any[] = []
        groups.forEach(group => {
          const list = group.cards
        if (list.length > 2) {
            // Create virtual group node with stable key id
            grouped.push({
              id: `group:${n.id}:${group.key}`,
              title: group.title,
              __isGroup: true,
              __groupType: group.title,
              __groupTypeKey: group.key,
              __parentCardId: n.id,
              children: list.map(x => ({ ...x }))
            })
          } else {
          // Keep one or two cards flat
          grouped.push(...list)
          }
        })
      // Recurse both virtual group nodes and normal nodes
      node.children = grouped.map((x: any) => {
        const copy = { ...x }
        if (Array.isArray(copy.children) && copy.children.length > 0) {
          copy.children = buildGroupedNodes(copy.children as any)
        }
        return copy
      })
    }
    return node
  })
}

const groupedTree = computed(() => buildGroupedNodes(cardTree.value as unknown as any[]))

// Local State
const activeTab = ref('market')
const relationGraphRefreshSeq = ref(0)
const activeRightTab = ref('assistant')
const isCreateCardDialogVisible = ref(false)
const exportDialogVisible = ref(false)
const prefetchedContext = ref<any>(null)
const newCardForm = reactive<Partial<CardCreate>>({
  title: '',
  card_type_id: undefined,
  parent_id: '' as any
})

const selectedCardIds = ref<number[]>([])
const lastSelectedCardId = ref<number | null>(null)

const blankMenuVisible = ref(false)
const blankMenuX = ref(0)
const blankMenuY = ref(0)
const blankMenuRef = ref<HTMLElement | null>(null)

// Search State
const searchQuery = ref('')
const searchResults = ref<CardRead[]>([])
const isSearching = computed(() => searchQuery.value.trim().length > 0)
const searchLoading = ref(false)

const handleSearch = debounce(async (query: string) => {
  if (!query.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const pid = projectStore.currentProject?.id
    if (pid) {
      searchResults.value = await searchCards(pid, query)
    }
  } catch (e) {
    console.error(e)
  } finally {
    searchLoading.value = false
  }
}, 300)

// Composables
const { leftSidebarWidth, rightSidebarWidth, startResizing } = useSidebarResizer()
const { t } = useI18n()
const localeStore = useLocaleStore()
const trRuntime = (value?: any) => String(value || '')
const isLeftSidebarVisible = ref(true)
const leftSidebarDisplayWidth = computed(() => (isLeftSidebarVisible.value ? leftSidebarWidth.value : 0))
const leftSidebarToggleOffset = computed(() => (isLeftSidebarVisible.value ? Math.max(leftSidebarDisplayWidth.value - 18, 8) : 10))

function toggleLeftSidebar() {
  isLeftSidebarVisible.value = !isLeftSidebarVisible.value
}

 const treeSelectProps = {
   value: 'id',
   label: 'title',
   children: 'children'
 } as const

 const typesPaneHeight = ref(180)
 const innerResizerThickness = 6

 function startResizingInner() {
   const startY = (event as MouseEvent).clientY
   const startH = typesPaneHeight.value
   const onMove = (e: MouseEvent) => {
     const dy = e.clientY - startY
     const next = Math.max(120, Math.min(startH + dy, 400))
     typesPaneHeight.value = next
   }
   const onUp = () => {
     window.removeEventListener('mousemove', onMove)
     window.removeEventListener('mouseup', onUp)
   }
   window.addEventListener('mousemove', onMove)
   window.addEventListener('mouseup', onUp)
 }

function onTypeDragStart(t: any) {
  try { (event as DragEvent).dataTransfer?.setData('application/x-card-type-id', String(t.id)) } catch {}
}
async function onCardsPaneDrop(e: DragEvent) {
 try {
   const typeId = e.dataTransfer?.getData('application/x-card-type-id')
   if (typeId) {
     newCardForm.title = (cardStore.cardTypes.find(ct => ct.id === Number(typeId))?.name || t('editor.defaults.new_card'))
     newCardForm.card_type_id = Number(typeId)
     newCardForm.parent_id = '' as any
     handleCreateCard()
     return
   }
   const freeCardId = e.dataTransfer?.getData('application/x-free-card-id')
   if (freeCardId) {
     await copyCard(Number(freeCardId), { target_project_id: projectStore.currentProject!.id, parent_id: null as any })
     await cardStore.fetchCards(projectStore.currentProject!.id)
     ElMessage.success(t('editor.messages.copied_free_card_to_root'))
     return
   }
 } catch {}
}

async function onTypesPaneDrop(e: DragEvent) {
 try {
   const cardIdStr = e.dataTransfer?.getData('application/x-card-id')
   const cardId = cardIdStr ? Number(cardIdStr) : NaN
   if (!cardId || Number.isNaN(cardId)) return
   const resp = await getCardSchema(cardId)
   const effective = resp?.effective_schema || resp?.json_schema
   if (!effective) { ElMessage.warning(t('editor.messages.no_structure_for_type_generation')); return }
   const old = cards.value.find(c => (c as any).id === cardId)
   const defaultName = (old?.title || t('editor.defaults.new_type')) as string
   const { value } = await ElMessageBox.prompt(t('editor.messages.create_type_from_instance_prompt'), t('editor.messages.create_card_type'), {
     inputValue: defaultName,
     confirmButtonText: t('common.create'),
     cancelButtonText: t('common.cancel'),
     inputValidator: (v:string) => v.trim().length > 0 || t('editor.validation.name_required')
   })
   const finalName = String(value).trim()
   await createCardType({ name: finalName, description: t('editor.defaults.default_card_type_description', { name: finalName }), json_schema: effective } as any)
   ElMessage.success(t('editor.messages.created_card_type_from_instance'))
   await cardStore.fetchCardTypes()
 } catch (err) {
 }
}


function handleAllowDrag(draggingNode: any): boolean {
  if (draggingNode.data.__isGroup) {
    return false
  }
  return true
}

function handleAllowDrop(draggingNode: any, dropNode: any, type: 'prev' | 'inner' | 'next'): boolean {
  if (dropNode.data.__isGroup) {
    return type === 'inner'
  }

  return true
}

async function handleNodeDrop(
  draggingNode: any,
  dropNode: any,
  dropType: 'before' | 'after' | 'inner',
  ev: DragEvent
) {
  try {
    const draggedCard = draggingNode.data
    const targetCard = dropNode.data

    if (targetCard.__isGroup && dropType === 'inner') {
      const rootCards = cards.value.filter(c => c.parent_id === null)
      const maxOrder = rootCards.length > 0 ? Math.max(...rootCards.map(c => c.display_order || 0)) : -1

      await cardStore.modifyCard(draggedCard.id, {
        parent_id: null,
        display_order: maxOrder + 1
      }, { skipHooks: true })
      ElMessage.success(t('editor.messages.moved_to_root', { title: draggedCard.title }))
      await cardStore.fetchCards(projectStore.currentProject!.id)

      assistantStore.recordOperation(projectStore.currentProject!.id, {
        type: 'move',
        cardId: draggedCard.id,
        cardTitle: draggedCard.title,
        cardType: draggedCard.card_type?.name || 'Unknown',
        detail: t('editor.history.moved_from_child_to_root')
      })

      updateProjectStructureContext(activeCard.value?.id)
      return
    }

    if (dropType === 'inner') {
      const children = cards.value.filter(c => c.parent_id === targetCard.id)
      const maxOrder = children.length > 0 ? Math.max(...children.map(c => c.display_order || 0)) : -1

      await cardStore.modifyCard(draggedCard.id, {
        parent_id: targetCard.id,
        display_order: maxOrder + 1
      }, { skipHooks: true })
      ElMessage.success(t('editor.messages.moved_as_child', { title: draggedCard.title, target: targetCard.title }))
      await cardStore.fetchCards(projectStore.currentProject!.id)

      assistantStore.recordOperation(projectStore.currentProject!.id, {
        type: 'move',
        cardId: draggedCard.id,
        cardTitle: draggedCard.title,
        cardType: draggedCard.card_type?.name || 'Unknown',
        detail: t('editor.history.set_as_child_detail', { title: targetCard.title, type: targetCard.card_type?.name || 'Unknown', id: targetCard.id })
      })

      updateProjectStructureContext(activeCard.value?.id)
      return
    }

    const newParentId = targetCard.parent_id || null

    const siblings = cards.value
      .filter(c => (c.parent_id || null) === newParentId && c.id !== draggedCard.id)
      .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))

    const targetIndex = siblings.findIndex(c => c.id === targetCard.id)

    let newSiblings = [...siblings]
    if (dropType === 'before') {
      newSiblings.splice(targetIndex, 0, draggedCard)
    } else {
      newSiblings.splice(targetIndex + 1, 0, draggedCard)
    }

    const updates: Array<{ card_id: number; display_order: number; parent_id?: number | null }> = []

    newSiblings.forEach((card, index) => {
      if (card.id === draggedCard.id) {
        updates.push({
          card_id: card.id,
          display_order: index,
          parent_id: newParentId
        })
      } else if (card.display_order !== index) {
        updates.push({
          card_id: card.id,
          display_order: index,
          parent_id: card.parent_id || null
        })
      }
    })

    if (updates.length > 0) {
      const { batchReorderCards } = await import('@renderer/api/cards')
      await batchReorderCards({ updates })
    }

    ElMessage.success(t('editor.messages.reordered_card', { title: draggedCard.title }))
    await cardStore.fetchCards(projectStore.currentProject!.id)

    const targetCardTitle = targetCard?.title || t('editor.defaults.root')
    const positionText = dropType === 'before' ? t('editor.position.before') : t('editor.position.after')
    let moveDetail = t('editor.history.moved_to_position', { title: targetCardTitle, position: positionText })

    if (draggedCard.parent_id !== newParentId) {
      const cardMap = new Map(cards.value.map(c => [(c as any).id, c.title]))
      const oldParentName = draggedCard.parent_id
        ? cardMap.get(draggedCard.parent_id) || t('common.unknown')
        : t('editor.defaults.root')
      const newParentName = newParentId
        ? cardMap.get(newParentId) || t('common.unknown')
        : t('editor.defaults.root')
      moveDetail += ` (${t('editor.history.moved_parent_change', { oldParent: oldParentName, newParent: newParentName })})`
    }

    assistantStore.recordOperation(projectStore.currentProject!.id, {
      type: 'move',
      cardId: draggedCard.id,
      cardTitle: draggedCard.title,
      cardType: draggedCard.card_type?.name || 'Unknown',
      detail: moveDetail
    })

    updateProjectStructureContext(activeCard.value?.id)

  } catch (err: any) {
    console.error(t('editor.messages.drag_failed'), err)
    ElMessage.error(err?.message || t('editor.messages.drag_failed'))
    await cardStore.fetchCards(projectStore.currentProject!.id)
    updateProjectStructureContext(activeCard.value?.id)
  }
}


function getDraggedTypeId(e: DragEvent): number | null {
 try {
   const raw = e.dataTransfer?.getData('application/x-card-type-id') || ''
   const n = Number(raw)
   return Number.isFinite(n) && n > 0 ? n : null
 } catch { return null }
}

async function onExternalDropToNode(e: DragEvent, nodeData: any) {
 const typeId = getDraggedTypeId(e)
 if (typeId) {
   if (nodeData?.__isGroup) return
   const newCard = await cardStore.addCard({ title: t('editor.defaults.new_card'), card_type_id: typeId, parent_id: nodeData?.id } as any)

   if (newCard && projectStore.currentProject?.id) {
     const cardType = cardStore.cardTypes.find(ct => ct.id === typeId)
     assistantStore.recordOperation(projectStore.currentProject.id, {
       type: 'create',
       cardId: (newCard as any).id,
       cardTitle: newCard.title,
       cardType: cardType?.name || 'Unknown'
     })
   }

   return
 }

 try {
   const freeCardId = e.dataTransfer?.getData('application/x-free-card-id')
   if (freeCardId) {
     if (nodeData?.__isGroup) return
     await copyCard(Number(freeCardId), { target_project_id: projectStore.currentProject!.id, parent_id: Number(nodeData?.id) })
     await cardStore.fetchCards(projectStore.currentProject!.id)
     ElMessage.success(t('editor.messages.copied_free_card_to_node'))
     return
   }
 } catch (err) {
   console.error(t('editor.messages.drag_failed'), err)
 }
}

 // --- Methods ---

function handleNodeClick(data: any) {
  if (data.__isGroup) return

  selectedCardIds.value = [data.id]
  lastSelectedCardId.value = data.id

  cardStore.setActiveCard(data.id)
  assistantSelectionCleared.value = false
  activeTab.value = 'editor'
  try {
    const pid = projectStore.currentProject?.id as number
    const pname = projectStore.currentProject?.name || ''
    const full = (cards.value || []).find((c:any) => c.id === data.id)
    const title = (full?.title || data.title || '') as string
    const content = (full?.content || (data as any).content || {})
    if (pid && data?.id) {
      assistantStore.addAutoRef({
        refType: 'card',
        projectId: pid,
        projectName: pname,
        cardId: data.id,
        cardTitle: title,
        content,
      })
    }
  } catch {}
}

function handleCardClick(event: MouseEvent, data: any) {
  if (data.__isGroup) {
    handleNodeClick(data)
    return
  }

  const cardId = data.id

  if (event.ctrlKey || event.metaKey) {
    const index = selectedCardIds.value.indexOf(cardId)
    if (index > -1) {
      selectedCardIds.value.splice(index, 1)
    } else {
      selectedCardIds.value.push(cardId)
    }
    lastSelectedCardId.value = cardId
    event.stopPropagation()
    return
  }

  if (event.shiftKey && lastSelectedCardId.value !== null) {
    const flatCards: number[] = []
    function flattenTree(nodes: any[]) {
      for (const node of nodes) {
        if (!node.__isGroup && node.id) {
          flatCards.push(node.id)
        }
        if (node.children && node.children.length > 0) {
          flattenTree(node.children)
        }
      }
    }
    flattenTree(groupedTree.value)

    const startIndex = flatCards.indexOf(lastSelectedCardId.value)
    const endIndex = flatCards.indexOf(cardId)

    if (startIndex !== -1 && endIndex !== -1) {
      const minIndex = Math.min(startIndex, endIndex)
      const maxIndex = Math.max(startIndex, endIndex)

      selectedCardIds.value = flatCards.slice(minIndex, maxIndex + 1)
    }

    event.stopPropagation()
    return
  }

  handleNodeClick(data)
}

function isCardSelected(cardId: number): boolean {
  return selectedCardIds.value.includes(cardId)
}

async function batchDeleteCards() {
  if (selectedCardIds.value.length === 0) {
    ElMessage.warning(t('editor.messages.select_cards_to_delete_first'))
    return
  }

  try {
    await ElMessageBox.confirm(
      t('editor.messages.confirm_delete_selected_cards', { count: selectedCardIds.value.length }),
      t('editor.messages.batch_delete_confirm_title'),
      { type: 'warning' }
    )

    const deletedCards = selectedCardIds.value.map(id => {
      const card = cards.value.find(c => (c as any).id === id)
      return {
        id,
        title: card?.title || t('common.unknown'),
        cardType: (card as any)?.card_type?.name || 'Unknown'
      }
    })

    if (activeCard.value && selectedCardIds.value.includes((activeCard.value as any).id)) {
      cardStore.setActiveCard(null as any)
    }

    const selectedSet = new Set(selectedCardIds.value)
    const cardsToDelete: number[] = []

    function isDescendantOfSelected(cardId: number): boolean {
      const card = cards.value.find(c => (c as any).id === cardId)
      if (!card) return false

      let parentId = (card as any).parent_id
      while (parentId) {
        if (selectedSet.has(parentId)) {
          return true
        }
        const parent = cards.value.find(c => (c as any).id === parentId)
        if (!parent) break
        parentId = (parent as any).parent_id
      }
      return false
    }

    for (const cardId of selectedCardIds.value) {
      if (!isDescendantOfSelected(cardId)) {
        cardsToDelete.push(cardId)
      }
    }

    let successCount = 0
    for (const cardId of cardsToDelete) {
      try {
        await cardStore.removeCard(cardId)
        successCount++
      } catch (error: any) {
        ElMessage.error(t('editor.messages.delete_card_failed_with_reason', { reason: error.message || t('editor.messages.unknown_error') }))
      }
    }

    if (projectStore.currentProject?.id) {
      for (const card of deletedCards) {
        assistantStore.recordOperation(projectStore.currentProject.id, {
          type: 'delete',
          cardId: card.id,
          cardTitle: card.title,
          cardType: card.cardType
        })
      }
    }

    selectedCardIds.value = []
    lastSelectedCardId.value = null

    ElMessage.success(t('editor.messages.deleted_cards_count', { count: selectedCardIds.value.length || deletedCards.length }))
  } catch (e) {
  }
}

watch(activeCard, (c) => {
 try {
   if (!c) return
   const pid = projectStore.currentProject?.id as number
   const pname = projectStore.currentProject?.name || ''
  assistantStore.addAutoRef({
    refType: 'card',
    projectId: pid,
    projectName: pname,
    cardId: (c as any).id,
    cardTitle: (c as any).title || '',
    content: (c as any).content || {},
  })

   assistantStore.updateActiveCard(c as any, pid)

   updateProjectStructureContext((c as any)?.id)
 } catch (err) {
 }
})

watch(() => projectStore.currentProject, (newProject) => {
  if (!newProject?.id) return

  searchQuery.value = ''
  searchResults.value = []

  try {
    assistantStore.loadOperations(newProject.id)

    assistantStore.updateProjectCardTypes(cardStore.cardTypes.map(ct => ct.name))

    updateProjectStructureContext(activeCard.value?.id)
  } catch (err) {
  }
}, { immediate: true })

watch(() => cards.value.length, () => {
  try {
    updateProjectStructureContext(activeCard.value?.id)
  } catch (err) {
  }
})

function updateProjectStructureContext(currentCardId?: number) {
  const project = projectStore.currentProject
  if (!project?.id) return

  assistantStore.updateProjectStructure(
    project.id,
    project.name,
    cards.value,
    cardStore.cardTypes,
    currentCardId
  )
}

function onNodeExpand(_: any, node: any) {
  editorStore.addExpandedKey(String(node.key))
}

function onNodeCollapse(_: any, node: any) {
  const removeRecursively = (n: any) => {
    if (n.key) {
      editorStore.removeExpandedKey(String(n.key))
    }
    if (n.childNodes && n.childNodes.length > 0) {
      n.childNodes.forEach((child: any) => removeRecursively(child))
    }
  }
  removeRecursively(node)
}

function handleEditCard(cardId: number) {
  cardStore.setActiveCard(cardId);
  activeTab.value = 'editor';
}

async function handleCreateCard() {
  if (!newCardForm.title || !newCardForm.card_type_id) {
    ElMessage.warning(t('editor.messages.fill_card_title_and_type'));
    return;
  }
  const payload: any = {
    ...newCardForm,
    parent_id: (newCardForm as any).parent_id === '' ? undefined : (newCardForm as any).parent_id
  }
  const newCard = await cardStore.addCard(payload as CardCreate);

  if (newCard && projectStore.currentProject?.id) {
    const cardType = cardStore.cardTypes.find(ct => ct.id === newCardForm.card_type_id)
    assistantStore.recordOperation(projectStore.currentProject.id, {
      type: 'create',
      cardId: (newCard as any).id,
      cardTitle: newCard.title,
      cardType: cardType?.name || 'Unknown'
    })
  }

  isCreateCardDialogVisible.value = false;
  Object.assign(newCardForm, { title: '', card_type_id: undefined, parent_id: '' as any });
}

function getIconByCardType(cardTypeOrKey?: any) {
  const typeKey = typeof cardTypeOrKey === 'string' ? cardTypeOrKey : getCardTypeKey(cardTypeOrKey)
  switch (typeKey) {
    case 'work_tags':
      return CollectionTag
    case 'special_ability':
      return MagicStick
    case 'one_sentence':
      return ChatLineRound
    case 'story_outline':
      return List
    case 'world_building':
      return Connection
    case 'blueprint':
      return Tickets
    case 'volume_outline':
      return Notebook
    case 'chapter_outline':
    case 'chapter_body':
    case 'general_text':
      return Document
    case 'character_card':
      return User
    case 'scene_card':
      return OfficeBuilding
    case 'organization_card':
      return Connection
    case 'item_card':
      return Box
    case 'concept_card':
      return CollectionTag
    case 'folder':
      return Folder
    default:
      return Document
  }
}

function handleContextCommand(command: string, data: any) {
  if (command === 'create-child') {
    openCreateChild(data.id)
  } else if (command === 'create-child-in-group') {
    openCreateChildInGroup(data.__parentCardId, data.__groupType, data.__groupTypeKey)
  } else if (command === 'delete') {
    deleteNode(data.id, data.title)
  } else if (command === 'batch-delete') {
    batchDeleteCards()
  } else if (command === 'delete-group') {
    deleteGroupNodes(data)
  } else if (command === 'edit-structure') {
     if (!data?.id || data.__isGroup) return
     openCardSchemaStudio(data)
  } else if (command === 'rename') {
    if (!data?.id || data.__isGroup) return
    renameCard(data.id, data.title || '')
  } else if (command === 'add-as-reference') {
    try {
      if (!data?.id || data.__isGroup) return
      const pid = projectStore.currentProject?.id as number
      const pname = projectStore.currentProject?.name || ''
      const full = (cards.value || []).find((c:any) => c.id === data.id)
      const title = (full?.title || data.title || '') as string
      const content = (full?.content || (data as any).content || {})
      assistantStore.addInjectedRefDirect({
        refType: 'card',
        projectId: pid,
        projectName: pname,
        cardId: data.id,
        cardTitle: title,
        content,
      }, 'manual')
      ElMessage.success(t('editor.messages.added_as_reference'))
    } catch {}
  }
}

function openCardSchemaStudio(card: any) {
  schemaStudio.value = { visible: true, cardId: card.id, cardTitle: card.title || '' }
}

const schemaStudio = ref<{ visible: boolean; cardId: number; cardTitle: string }>({ visible: false, cardId: 0, cardTitle: '' })

async function onCardSchemaSaved() {
  try {
    await cardStore.fetchCards(projectStore.currentProject?.id as number)
  } catch {}
}

function openCreateCardDialog(options?: { title?: string; cardTypeName?: string; cardTypeKey?: string; parentId?: number | null }) {
  newCardForm.title = options?.title || ''
  newCardForm.parent_id = options?.parentId == null ? '' as any : options.parentId as any
  if (options?.cardTypeKey || options?.cardTypeName) {
    const cardType = cardStore.cardTypes.find(ct =>
      (options?.cardTypeKey && getCardTypeKey(ct) === options.cardTypeKey) ||
      (options?.cardTypeName && ct.name === options.cardTypeName)
    )
    newCardForm.card_type_id = cardType?.id
  } else {
    newCardForm.card_type_id = undefined
  }
  activeTab.value = 'editor'
  isCreateCardDialogVisible.value = true
  blankMenuVisible.value = false
}

function openCreateChild(parentId: number) {
  openCreateCardDialog({ parentId })
}

function openCreateChildInGroup(parentId: number, groupType: string, groupTypeKey?: string) {
  openCreateCardDialog({ parentId, cardTypeName: groupType, cardTypeKey: groupTypeKey })
}

function openCreateRoot() {
  openCreateCardDialog()
}

function onOpenCreateCardEvent(e: Event) {
  const detail = (e as CustomEvent)?.detail || {}
  openCreateCardDialog({
    title: typeof detail.title === 'string' ? detail.title : '',
    cardTypeName: typeof detail.cardTypeName === 'string' ? detail.cardTypeName : '',
    cardTypeKey: typeof detail.cardTypeKey === 'string' ? detail.cardTypeKey : '',
    parentId: Number.isFinite(Number(detail.parentId)) ? Number(detail.parentId) : null,
  })
}

function onSidebarContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.closest('.custom-tree-node')) return
  blankMenuX.value = e.clientX
  blankMenuY.value = e.clientY
  blankMenuVisible.value = true
}

async function deleteNode(cardId: number, title: string) {
  try {
    await ElMessageBox.confirm(t('editor.messages.confirm_delete_card', { title }), t('editor.messages.delete_confirm_title'), { type: 'warning' })

    const card = cards.value.find(c => (c as any).id === cardId)
    const cardType = card ? ((card as any).card_type?.name || 'Unknown') : 'Unknown'

    if (activeCard.value && (activeCard.value as any).id === cardId) {
      cardStore.setActiveCard(null as any)
    }

    try {
      await cardStore.removeCard(cardId)
      ElMessage.success(t('editor.messages.card_deleted'))

      if (projectStore.currentProject?.id) {
        assistantStore.recordOperation(projectStore.currentProject.id, {
          type: 'delete',
          cardId,
          cardTitle: title,
          cardType
        })
      }
    } catch (error: any) {
      ElMessage.error(t('editor.messages.delete_card_failed'))
    }
  } catch (e) {
  }
}

async function deleteGroupNodes(groupData: any) {
  try {
    const title = groupData?.title || groupData?.__groupType || t('editor.context.group_fallback')
    await ElMessageBox.confirm(t('editor.messages.confirm_delete_group_cards', { title }), t('editor.messages.delete_confirm_title'), { type: 'warning' })
    const directChildren: any[] = Array.isArray(groupData?.children) ? groupData.children : []
    const toDeleteOrdered: number[] = []

    function collectDescendantIds(parentId: number) {
      const childIds = (cards.value || []).filter((c: any) => c.parent_id === parentId).map((c: any) => c.id)
      for (const cid of childIds) collectDescendantIds(cid)
      toDeleteOrdered.push(parentId)
    }

    for (const child of directChildren) {
      collectDescendantIds(child.id)
    }

    const seen = new Set<number>()
    for (const id of toDeleteOrdered) {
      if (seen.has(id)) continue
      seen.add(id)
      await cardStore.removeCard(id)
    }
  } catch (e) {
  }
}

async function renameCard(cardId: number, oldTitle: string) {
  try {
    const { value } = await ElMessageBox.prompt(t('editor.messages.rename_prompt'), t('editor.messages.rename_title'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputPlaceholder: t('editor.create_dialog.card_title_placeholder'),
      inputValidator: (v:string) => v.trim().length > 0 || t('editor.validation.title_required')
    })
    const newTitle = String(value || '').trim()
    if (!newTitle) return
    if (newTitle === oldTitle) return
    const card = (cards.value || []).find((c: any) => c.id === cardId) as any
    const payload: any = { title: newTitle }

    const typeName = card?.card_type?.name || ''
    if ((typeName === String(t('codemirror.preview.relationSummary')) || typeName === String(t('codemirror.relationSummary'))) && card?.content) {
      const content: any = { ...(card.content as any) }
      content.title = newTitle
      payload.content = content
    }
    await cardStore.modifyCard(cardId, payload)
    ElMessage.success(t('editor.messages.renamed'))
  } catch {
    // user canceled or failed
  }
}

const assistantResolvedContext = ref<string>('')
const assistantEffectiveSchema = ref<any>(null)
const assistantSelectionCleared = ref<boolean>(false)

const assistantParams = ref<{ llm_config_id: number | null; prompt_name: string | null; temperature: number | null; max_tokens: number | null; timeout: number | null }>({ llm_config_id: null, prompt_name: t('assistant.default_prompt'), temperature: null, max_tokens: null, timeout: null })
const isChapterContent = computed(() => {
  return isCardType(activeCard.value?.card_type, 'chapter_body')
})

const showRightSidebarTabs = computed(() => {
  return Boolean(activeCard.value)
})

const reviewTargetCardIdForSidebar = computed<number | null>(() => {
  const card = activeCard.value as any
  if (!card) return null
  if (isCardType(card?.card_type, 'review_result_card')) {
    const target = Number(card?.content?.review_target_card_id || 0)
    return Number.isFinite(target) && target > 0 ? target : null
  }
  return Number(card.id || 0) || null
})

const rightSidebarTabNames = computed(() => {
  if (!showRightSidebarTabs.value) return [] as string[]
  if (isChapterContent.value) return ['assistant', 'context', 'extract', 'outline', 'review-history']
  return ['assistant', 'review-history']
})

const chapterVolumeNumber = computed(() => {
  if (!isChapterContent.value) return null
  const content: any = activeCard.value?.content || {}
  return content.volume_number ?? null
})

const chapterChapterNumber = computed(() => {
  if (!isChapterContent.value) return null
  const content: any = activeCard.value?.content || {}
  return content.chapter_number ?? null
})

const chapterParticipants = computed(() => {
  if (!isChapterContent.value) return []
  const content: any = activeCard.value?.content || {}
  const list = content.entity_list || []
  if (Array.isArray(list)) {
    return list.map((x: any) => typeof x === 'string' ? x : (x?.name || '')).filter(Boolean).slice(0, 6)
  }
  return []
})

watch(isChapterContent, async (val) => {
  if (val && activeCard.value) {
    await assembleChapterContext()
  }
}, { immediate: true })

watch(rightSidebarTabNames, (tabNames) => {
  if (!tabNames.includes(activeRightTab.value)) {
    activeRightTab.value = 'assistant'
  }
}, { immediate: true })

watch(cards, async () => {
  if (isChapterContent.value && activeCard.value) {
    await assembleChapterContext()
  }
})

async function assembleChapterContext() {
  if (!isChapterContent.value || !projectStore.currentProject?.id) return

  try {
    const { assembleContext } = await import('@renderer/api/ai')
    const res = await assembleContext({
      project_id: projectStore.currentProject.id,
      volume_number: chapterVolumeNumber.value ?? undefined,
      chapter_number: chapterChapterNumber.value ?? undefined,
      participants: chapterParticipants.value,
      current_draft_tail: ''
    })
    prefetchedContext.value = res
  } catch (e) {
    console.error('Failed to assemble chapter context:', e)
  }
}

async function handleContextParticipantsUpdate(names: string[]) {
  try {
    if (!isChapterContent.value || !activeCard.value) return
    const card = activeCard.value as any
    const content: any = { ...(card.content || {}) }
    const normalized = (names || [])
      .map(n => (typeof n === 'string' ? n.trim() : String(n || '')).trim())
      .filter(Boolean)
    content.entity_list = normalized
    await cardStore.modifyCard(card.id, { content } as any)
  } catch (e) {
    console.error('Failed to update participants on card:', e)
  }
}

function handleContextAssembledUpdate(ctx: any) {
  prefetchedContext.value = ctx || null
}


async function refreshAssistantContext() {
  try {
    const card = assistantSelectionCleared.value ? null : (activeCard.value as any)
    if (!card) { assistantResolvedContext.value = ''; assistantEffectiveSchema.value = null; return }
    const { resolveTemplate } = await import('@renderer/services/contextResolver')
    const resolved = resolveTemplate({
      template: card.ai_context_template || '',
      cards: cards.value,
      currentCard: card,
      assembledContext: prefetchedContext.value,
    })
    assistantResolvedContext.value = resolved
    const resp = await getCardSchema(card.id)
    assistantEffectiveSchema.value = resp?.effective_schema || resp?.json_schema || null
    try {
      const ai = await getCardAIParams(card.id)
      const eff = (ai?.effective_params || {}) as any
      assistantParams.value = {
        llm_config_id: eff.llm_config_id ?? null,
        prompt_name: (eff.prompt_name ?? t('assistant.default_prompt')) as any,
        temperature: eff.temperature ?? null,
        max_tokens: eff.max_tokens ?? null,
        timeout: eff.timeout ?? null,
      }
    } catch {
      const p = (card?.ai_params || {}) as any
      assistantParams.value = {
        llm_config_id: p.llm_config_id ?? null,
        prompt_name: (p.prompt_name ?? t('assistant.default_prompt')) as any,
        temperature: p.temperature ?? null,
        max_tokens: p.max_tokens ?? null,
        timeout: p.timeout ?? null,
      }
    }
  } catch { assistantResolvedContext.value = '' }
}

watch(activeCard, () => { if (!assistantSelectionCleared.value) refreshAssistantContext() })
watch(prefetchedContext, () => { if (!assistantSelectionCleared.value) refreshAssistantContext() })

watch(activeTab, (tab) => {
  if (tab === 'relation-graph') {
    relationGraphRefreshSeq.value += 1
  }
})

function resetAssistantSelection() {
  assistantSelectionCleared.value = true
  assistantResolvedContext.value = ''
  assistantEffectiveSchema.value = null
}

const assistantFinalize = async (summary: string) => {
  try {
    const card = activeCard.value as any
    if (!card) return
    const evt = new CustomEvent('nf:assistant-finalize', { detail: { cardId: card.id, summary } })
    window.dispatchEvent(evt)
    ElMessage.success(t('editor.messages.final_notes_sent'))
  } catch {}
}

function onAssistantAddRef(e: CustomEvent) {
  try {
    const payload = (e as any)?.detail || {}
    const ref = (payload.ref || payload) as AssistantRef
    assistantStore.addInjectedRefDirect(ref, (ref as any)?.source || 'manual')
    activeRightTab.value = 'assistant'
  } catch {}
}

function onAssistantAddExcerptRef(e: CustomEvent) {
  try {
    const payload = (e as any)?.detail || {}
    const ref = (payload.ref || payload) as ChapterExcerptRef
    assistantStore.addChapterExcerptRef(ref, (ref as any)?.source || 'manual')
    activeRightTab.value = 'assistant'
  } catch {}
}

function onAssistantAddReviewRef(e: CustomEvent) {
  try {
    const payload = (e as any)?.detail || {}
    const ref = (payload.ref || payload) as ReviewResultRef
    assistantStore.addReviewResultRef(ref, (ref as any)?.source || 'manual')
    activeRightTab.value = 'assistant'
  } catch {}
}

async function onAssistantFinalize(e: CustomEvent) {
  try {
    const card = activeCard.value as any
    if (!card) return
    const summary: string = (e as any)?.detail?.summary || ''
    const llmId = assistantParams.value.llm_config_id
    const promptName = (assistantParams.value.prompt_name || t('generation.defaults.prompt_name')) as string
    const schema = assistantEffectiveSchema.value
    const ctx = assistantResolvedContext.value || ''
    if (!llmId) { ElMessage.warning(t('editor.messages.select_model_first')); return }
    if (!schema) { ElMessage.warning(t('editor.messages.no_valid_schema_finalize')); return }
    const inputText = [
      ctx ? `${t('editor.messages.finalize_context_label')}\n${ctx}` : '',
      summary ? `${t('editor.messages.finalize_notes_label')}\n${summary}` : '',
    ].filter(Boolean).join('\n\n')
    const result = await generateAIContent({
      input: { input_text: inputText },
      llm_config_id: llmId as any,
      prompt_name: promptName,
      response_model_schema: schema as any,
      temperature: assistantParams.value.temperature ?? undefined,
      max_tokens: assistantParams.value.max_tokens ?? undefined,
      timeout: assistantParams.value.timeout ?? undefined,
    } as any)
    if (result) {
      await cardStore.modifyCard(card.id, { content: result as any })
      ElMessage.success(t('editor.messages.finalize_written_back'))
    } else {
      ElMessage.error(t('editor.messages.finalize_failed_no_content'))
    }
  } catch (err:any) {
    console.error(err)
    ElMessage.error(t('editor.messages.finalize_failed'))
  }
}
async function handleJumpToCard(payload: { projectId: number; cardId: number }) {
  try {
    const curPid = projectStore.currentProject?.id
    if (curPid !== payload.projectId) {
      const all = await getProjects()
      const target = (all || []).find(p => p.id === payload.projectId)
      if (target) {
        projectStore.setCurrentProject(target as any)
        await cardStore.fetchCards(target.id!)
      }
    }
    cardStore.setActiveCard(payload.cardId)
    activeTab.value = 'editor'
  } catch {}
}

function onJumpToCardEvent(e: CustomEvent) {
  const detail = (e as any)?.detail || {}
  const cardId = Number(detail.cardId || 0)
  if (!cardId) return
  void handleJumpToCard({
    projectId: Number(detail.projectId || projectStore.currentProject?.id || 0),
    cardId,
  })
}

// --- Lifecycle ---

onMounted(async () => {
  // Fetch initial data for the card system (like types and models)
  // Cards will be fetched automatically by the watcher in the card store
  await cardStore.fetchInitialData()
  await cardStore.fetchAvailableModels()

  try {
    const types = cardStore.cardTypes.map(t => t.name)
    assistantStore.updateProjectCardTypes(types)
  } catch {}

  window.addEventListener('nf:navigate', onNavigate as any)
  window.addEventListener('nf:assistant-finalize', onAssistantFinalize as any)
  window.addEventListener('nf:switch-main-tab', onSwitchMainTab as any)
  window.addEventListener('nf:switch-right-tab', onSwitchRightTab as any)
  window.addEventListener('nf:assistant-add-ref', onAssistantAddRef as any)
  window.addEventListener('nf:assistant-add-excerpt-ref', onAssistantAddExcerptRef as any)
  window.addEventListener('nf:assistant-add-review-ref', onAssistantAddReviewRef as any)
  window.addEventListener('nf:jump-to-card', onJumpToCardEvent as any)
  window.addEventListener('nf:open-create-card', onOpenCreateCardEvent as any)
  await refreshAssistantContext()
})

 onBeforeUnmount(() => {
   window.removeEventListener('nf:navigate', onNavigate as any)
   window.removeEventListener('nf:assistant-finalize', onAssistantFinalize as any)
   window.removeEventListener('nf:switch-main-tab', onSwitchMainTab as any)
   window.removeEventListener('nf:switch-right-tab', onSwitchRightTab as any)
   window.removeEventListener('nf:assistant-add-ref', onAssistantAddRef as any)
   window.removeEventListener('nf:assistant-add-excerpt-ref', onAssistantAddExcerptRef as any)
   window.removeEventListener('nf:assistant-add-review-ref', onAssistantAddReviewRef as any)
   window.removeEventListener('nf:jump-to-card', onJumpToCardEvent as any)
   window.removeEventListener('nf:open-create-card', onOpenCreateCardEvent as any)
  })

 function onNavigate(e: CustomEvent) {
   if ((e as any).detail?.to === 'market') {
     activeTab.value = 'market'
   }
 }

function onSwitchMainTab(e: CustomEvent) {
  const tab = (e as any)?.detail?.tab
  if (tab && ['market', 'editor', 'relation-graph'].includes(tab)) {
    activeTab.value = tab
  }
}

function onSwitchRightTab(e: CustomEvent) {
  const tab = (e as any)?.detail?.tab
  if (tab && rightSidebarTabNames.value.includes(tab)) {
    activeRightTab.value = tab
  }
}

 document.addEventListener('click', () => (blankMenuVisible.value = false))

 const treeRef = ref<any>(null)

 watch(groupedTree, async () => {
   // Wait for the tree to re-render with new data
   await nextTick()
   try {
     if (expandedKeys.value.length > 0) {
       // Using Element Plus Tree store API to set expanded keys
       // This is more reliable than manipulating nodes directly
       treeRef.value?.store?.setDefaultExpandedKeys(expandedKeys.value)
     }
   } catch (e) {
     console.error('Failed to restore expanded state:', e)
   }
 }, { deep: true })
</script>

<style scoped>
.full-row-dropdown { display: block; width: 100%; }
.blank-menu-ref { pointer-events: none; }

.editor-shell {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  min-height: 0;
}

.editor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
  flex-shrink: 0;
}

.editor-topbar__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.editor-topbar__title {
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
}

.editor-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  width: 100%;
  position: relative;
  background-color: var(--el-fill-color-lighter);
}

.sidebar {
  display: flex;
  flex-direction: column;
  background-color: var(--el-fill-color-lighter);
  transition: width 0.2s;
  flex-shrink: 0;
  overflow: hidden;
  border-right: none;
}

.card-navigation-sidebar {
  padding: 8px;
}

.sidebar-header { display: none; }

.sidebar-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.card-tree {
  background-color: transparent;
  flex-grow: 1;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  font-size: 14px;
  padding-right: 8px;
}
.card-icon {
  color: var(--el-text-color-secondary);
}
.child-count {
  margin-left: auto;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.resizer {
  width: 5px;
  background: transparent;
  cursor: col-resize;
  z-index: 10;
  user-select: none;
  position: relative;
  transition: background-color 0.2s;
}
.resizer:hover {
  background: var(--el-color-primary-light-7);
}

.main-content {
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  background-color: transparent;
}

.main-tabs {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--el-bg-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  overflow: hidden;
  border: none;
}

:deep(.el-tabs__content) {
  flex-grow: 1;
  overflow-y: auto;
}
:deep(.el-tab-pane) {
  height: 100%;
}

.custom-tree-node.full-row {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 3px 6px;
  border-radius: 4px;
  transition: background-color 0.2s;
}
.custom-tree-node.full-row .label {
  flex: 1;
}
.custom-tree-node.full-row.selected {
  background-color: var(--el-color-primary-light-9);
  border: 1px solid var(--el-color-primary-light-7);
}
.custom-tree-node.full-row.selected .label {
  color: var(--el-color-primary);
  font-weight: 500;
}


.types-pane { display: flex; flex-direction: column; border-bottom: 1px solid var(--el-border-color-light); background: var(--el-fill-color-lighter); padding: 6px; box-shadow: 0 2px 6px -2px var(--el-box-shadow-lighter); border-radius: 6px; }
.pane-title { font-size: 12px; color: var(--el-text-color-regular); font-weight: 600; padding: 2px 4px 6px 4px; }
.types-scroll { flex: 1; background: var(--el-fill-color-lighter); }
.types-list { list-style: none; padding: 0; margin: 0; }
.type-item { padding: 6px 8px; cursor: grab; display: flex; align-items: center; color: var(--el-text-color-primary); font-size: 13px; border-radius: 4px; }
.type-item:hover { background: var(--el-fill-color-light); color: var(--el-color-primary); }
.type-name { flex: 1; }

.inner-resizer { height: 6px; cursor: row-resize; background: var(--el-fill-color-light); border-top: 1px solid var(--el-border-color-light); border-bottom: 1px solid var(--el-border-color-light); transition: height .12s ease, background-color .12s ease, border-color .12s ease; }
.inner-resizer:hover { height: 8px; background: var(--el-fill-color); border-top: 1px solid var(--el-border-color); border-bottom: 1px solid var(--el-border-color); }
.cards-pane { position: relative; padding-top: 8px; overflow: auto; overflow-x: hidden; }
.cards-title {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
  padding: 8px;
  background: color-mix(in srgb, var(--el-bg-color) 92%, transparent);
  backdrop-filter: blur(14px);
  border: 1px solid color-mix(in srgb, var(--el-border-color-light) 82%, transparent);
  border-radius: 12px;
  margin: 0 2px 8px;
  box-shadow: 0 10px 24px -22px rgba(15, 23, 42, 0.45);
}
.cards-title-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.cards-title-text {
  min-width: 0;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cards-selection-chip {
  flex-shrink: 0;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1;
  color: var(--el-color-danger);
  background: color-mix(in srgb, var(--el-color-danger-light-9) 78%, var(--el-bg-color));
  border: 1px solid color-mix(in srgb, var(--el-color-danger-light-7) 82%, transparent);
}
.cards-title-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
}
.toolbar-action {
  width: 100%;
  min-width: 0;
  margin: 0 !important;
  justify-content: center;
}
.toolbar-action-create-full {
  grid-column: 1 / -1;
}
.toolbar-action-create-split {
  grid-column: span 1;
}
.toolbar-action-secondary {
  grid-column: span 1;
}
.toolbar-action-secondary--solo {
  grid-column: 1 / -1;
}
.toolbar-action-danger-split {
  grid-column: span 1;
}
.cards-title-actions :deep(.el-button > span) {
  min-width: 0;
}
.assistant-sidebar {
  border-left: none;
  background: transparent;
  flex-shrink: 0;
  padding: 16px 8px 16px 0;
}
.right-resizer { cursor: col-resize; width: 5px; background: transparent; }
.right-resizer:hover { background: var(--el-color-primary-light-7); }
.sidebar-edge-toggle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 30;
  display: grid;
  place-items: center;
  align-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--el-border-color) 84%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--el-bg-color) 94%, rgba(255,255,255,0.65));
  box-shadow:
    0 10px 22px -18px rgba(15, 23, 42, 0.34),
    0 3px 8px -6px rgba(15, 23, 42, 0.18);
  color: var(--el-text-color-regular);
  cursor: pointer;
  transition:
    left 0.2s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    color 0.18s ease,
    background-color 0.18s ease,
    transform 0.18s ease,
    opacity 0.18s ease;
  backdrop-filter: blur(14px);
  opacity: 0.92;
}
.sidebar-edge-toggle:hover,
.sidebar-edge-toggle:focus-visible {
  transform: translateY(-50%) scale(1.04);
  box-shadow:
    0 14px 28px -20px rgba(37, 99, 235, 0.28),
    0 4px 10px -8px rgba(15, 23, 42, 0.2);
  border-color: color-mix(in srgb, var(--el-color-primary-light-6) 68%, transparent);
  color: var(--el-color-primary);
  outline: none;
  opacity: 1;
}
.sidebar-edge-toggle.is-collapsed {
  background: color-mix(in srgb, var(--el-bg-color) 96%, rgba(255,255,255,0.72));
}
.sidebar-edge-toggle__icon {
  font-size: 15px;
  line-height: 1;
}
.nf-import-dialog :deep(.el-input__wrapper) { font-size: 14px; }
.nf-import-dialog :deep(.el-input__inner) { font-size: 14px; }
.nf-import-dialog :deep(.el-table .cell) { font-size: 14px; color: var(--el-text-color-primary); }
.nf-import-dialog :deep(.el-table__row) { height: 40px; }
.nf-tree-select-popper { min-width: 320px; }
.nf-tree-select-popper { background: var(--el-bg-color-overlay, #fff); color: var(--el-text-color-primary); }
.nf-tree-select-popper :deep(.el-select-dropdown__item) { color: var(--el-text-color-primary); }
.nf-tree-select-popper :deep(.el-tree) { background: transparent; }
.nf-tree-select-popper :deep(.el-tree-node__content) { background: transparent; }
.nf-tree-select-popper :deep(.el-tree-node__label) { font-size: 14px; color: var(--el-text-color-primary); }
.nf-tree-select-popper :deep(.is-current > .el-tree-node__content),
.nf-tree-select-popper :deep(.el-tree-node__content:hover) { background: var(--el-fill-color-light); }

.right-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.right-tabs :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 12px 12px 0 12px;
  background: var(--el-fill-color-lighter);
}
.right-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}
.right-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  font-weight: 500;
  padding: 0 16px;
  height: 36px;
  line-height: 36px;
}
.right-tabs :deep(.el-tabs__item.is-active) {
  color: var(--el-color-primary);
}
.right-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}
.right-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

.search-results-list {
  flex-grow: 1;
  overflow-y: auto;
  padding: 0 8px;
}
.search-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  color: var(--el-text-color-primary);
  font-size: 14px;
  transition: background-color 0.2s;
}
.search-item:hover {
  background-color: var(--el-fill-color-light);
}
.search-item-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
