<template>
  <div class="node-block-editor">
    <div class="node-blocks">
      <div
        v-for="(node, index) in nodes"
        :key="index"
        class="node-block"
        :class="{
          'is-selected': selectedIndex === index,
          'is-disabled': node.disabled
        }"
        @click="selectNode(index)"
        @dblclick="editNodeCode(index)"
      >
        <div class="node-block-header">
          <div class="node-info">
            <el-tag :type="getNodeCategoryColor(node.category)" size="small">
              {{ node.category }}
            </el-tag>
            <el-tag v-if="node.isAsync" type="warning" size="small" effect="dark">
              ? {{ t('node_block.async') }}
            </el-tag>
            <el-input
              v-if="editingVariable?.nodeIndex === index"
              v-model="editingVariable.value"
              size="small"
              style="width: 120px"
              @blur="saveVariableEdit"
              @keydown.enter.stop="saveVariableEdit"
              @keydown.esc="cancelVariableEdit"
              ref="variableInputRef"
            />
            <span
              v-else
              class="node-variable editable"
              @click.stop="startVariableEdit(index, node.variable)"
              :title="t('node_block.edit_variable_name')"
            >
              {{ node.variable }}
            </span>
            <span class="node-type">{{ node.nodeType }}</span>
          </div>
          <div class="node-actions">
            <el-tooltip :content="node.isAsync ? t('node_block.switch_to_sync') : t('node_block.switch_to_async')" placement="top">
              <el-button
                size="small"
                text
                @click.stop="toggleAsync(index)"
                :type="node.isAsync ? 'warning' : 'info'"
              >
                <template #icon>
                  <span style="font-size: 16px">{{ node.isAsync ? '⚡' : '🔄' }}</span>
                </template>
              </el-button>
            </el-tooltip>
            <el-tooltip :content="node.disabled ? t('node_block.enable_node') : t('node_block.disable_node')" placement="top">
              <el-switch
                v-model="node.disabled"
                @change="toggleNodeDisabled(index)"
                size="small"
                inactive-text=""
                active-text=""
                :active-value="true"
                :inactive-value="false"
                style="--el-switch-on-color: #909399; --el-switch-off-color: #67c23a"
                @click.stop
              />
            </el-tooltip>
            <el-tooltip :content="t('node_block.delete_node')" placement="top">
              <el-button
                size="small"
                text
                type="danger"
                @click.stop="deleteNode(index)"
                :icon="Delete"
              />
            </el-tooltip>
          </div>
        </div>

        <div v-if="node.description" class="node-description" @click.stop>
          {{ node.description }}
        </div>

        <div class="node-params" v-if="node.fields && node.fields.length > 0">
          <div class="params-header">
            <div class="params-title">{{ t('node_block.params') }}</div>
            <el-button
              text
              size="small"
              @click.stop="toggleNodeCollapse(index)"
              :icon="node.collapsed ? ArrowRight : ArrowDown"
            />
          </div>
          <div v-if="!node.collapsed" v-for="(field, fieldIndex) in node.fields" :key="field.name" class="param-item">
            <span class="param-key">{{ field.label }}:</span>
            <div class="param-value-wrapper">
              <div
                v-if="editingParam?.nodeIndex === index && editingParam?.fieldIndex === fieldIndex"
                class="smart-selector"
                style="flex: 1; display:flex; gap: 4px;"
              >
                <!-- ProjectSelect (x-component: ProjectSelect) -->
                <el-select
                  v-if="field.rawSchema?.['x-component'] === 'ProjectSelect'"
                  v-model="editingParam.value"
                  filterable
                  :allow-create="field.name === 'project_name'"
                  :default-first-option="field.name === 'project_name'"
                  :placeholder="t('node_block.select_project')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option
                    v-for="p in projectList"
                    :key="p.id"
                    :label="p.name"
                    :value="getProjectOptionValue(field, p)"
                  />
                </el-select>

                <!-- LLMSelect (x-component: LLMSelect) -->
                <el-select
                  v-else-if="field.rawSchema?.['x-component'] === 'LLMSelect'"
                  v-model="editingParam.value"
                  filterable
                  :allow-create="field.name === 'llm_name'"
                  :default-first-option="field.name === 'llm_name'"
                  :placeholder="t('node_block.select_llm_config')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option
                    v-for="cfg in llmConfigList"
                    :key="cfg.id"
                    :label="cfg.display_name || cfg.model_name"
                    :value="getLlmOptionValue(field, cfg)"
                  />
                </el-select>

                <!-- PromptSelect (x-component: PromptSelect) -->
                <el-select
                  v-else-if="field.rawSchema?.['x-component'] === 'PromptSelect'"
                  v-model="editingParam.value"
                  filterable
                  :placeholder="t('node_block.select_prompt')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option
                    v-for="prompt in promptList"
                    :key="prompt.id"
                    :label="prompt.name"
                    :value="prompt.id"
                  />
                </el-select>

                <!-- CardTypeSelect (x-component: CardTypeSelect) -->
                <el-select
                  v-else-if="field.rawSchema?.['x-component'] === 'CardTypeSelect'"
                  v-model="editingParam.value"
                  filterable
                  allow-create
                  default-first-option
                  :placeholder="t('node_block.card_type')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option
                    v-for="ct in cardTypeList"
                    :key="ct.id"
                    :label="ct.name"
                    :value="ct.key || ct.name"
                  />
                </el-select>

                <!-- ResponseModelSelect (x-component: ResponseModelSelect) -->
                <el-select
                  v-else-if="field.rawSchema?.['x-component'] === 'ResponseModelSelect'"
                  v-model="editingParam.value"
                  filterable
                  :placeholder="t('node_block.select_response_model')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option-group :label="t('node_block.builtin_models')">
                    <el-option
                      v-for="model in builtinResponseModels"
                      :key="model"
                      :value="model"
                      :label="model"
                    />
                  </el-option-group>
                  <el-option-group :label="t('node_block.custom_card_types')">
                    <el-option
                      v-for="ct in cardTypeList"
                      :key="ct.id"
                      :label="ct.name"
                      :value="ct.key || ct.name"
                    />
                  </el-option-group>
                </el-select>

                <!-- Textarea (x-component: Textarea) -->
                <el-input
                  v-else-if="field.rawSchema?.['x-component'] === 'Textarea'"
                  v-model="editingParam.value"
                  type="textarea"
                  :rows="4"
                  size="small"
                  :placeholder="t('node_block.input_content')"
                  @blur="saveParamEdit"
                />

                <!-- CodeEditor (x-component: CodeEditor) -->
                <el-input
                  v-else-if="field.rawSchema?.['x-component'] === 'CodeEditor'"
                  v-model="editingParam.value"
                  type="textarea"
                  :rows="6"
                  size="small"
                  class="code-expression-input"
                  :placeholder="t('node_block.input_python_expression')"
                  @blur="saveParamEdit"
                  @keydown.ctrl.enter.stop="saveParamEdit"
                />

                <!-- ToolMultiSelect (x-component: ToolMultiSelect) -->
                <el-select
                  v-else-if="field.rawSchema?.['x-component'] === 'ToolMultiSelect'"
                  v-model="editingParam.value"
                  filterable
                  multiple
                  collapse-tags
                  :placeholder="t('node_block.select_tool')"
                  size="small"
                  @change="saveParamEdit"
                >
                  <el-option value="search_cards" :label="t('node_block.tools.search_cards')" />
                  <el-option value="create_card" :label="t('node_block.tools.create_card')" />
                  <el-option value="update_card" :label="t('node_block.tools.update_card')" />
                  <el-option value="delete_card" :label="t('node_block.tools.delete_card')" />
                  <el-option value="get_card" :label="t('node_block.tools.get_card')" />
                  <el-option value="list_cards" :label="t('node_block.tools.list_cards')" />
                </el-select>

                <!-- Case 5: Boolean Switch -->
                <el-switch
                  v-else-if="field.type === 'boolean'"
                  v-model="editingParam.value"
                  size="small"
                  @change="saveParamEdit"
                />

                <!-- Case 6: Array Input (dynamic list) -->
                <div v-else-if="field.type === 'array'" style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
                  <div
                    v-for="(item, itemIndex) in editingParam.arrayItems"
                    :key="itemIndex"
                    style="display: flex; gap: 4px;"
                  >
                    <el-input
                      v-model="editingParam.arrayItems[itemIndex]"
                      size="small"
                      :placeholder="t('node_block.input_value')"
                      style="flex: 1;"
                    />
                    <el-button
                      size="small"
                      type="danger"
                      :icon="Delete"
                      @click.stop="removeArrayItem(itemIndex)"
                    />
                  </div>
                  <el-button
                    size="small"
                    type="primary"
                    :icon="Plus"
                    @click.stop="addArrayItem"
                  >
                    {{ t('common.add') }}
                  </el-button>
                  <el-button
                    size="small"
                    type="success"
                    @click.stop="saveParamEdit"
                  >
                    {{ t('common.save') }}
                  </el-button>
                </div>

                <!-- Case 7: Default Text Input -->
                <el-input
                  v-else
                  v-model="editingParam.value"
                  size="small"
                  @blur="saveParamEdit"
                  @keydown.enter.stop="saveParamEdit"
                >
                  <!-- Folder selection trigger for DirectorySelect -->
                  <template #append v-if="field.rawSchema?.['x-component'] === 'DirectorySelect'">
                    <el-button :icon="Folder" @click.stop="openFolderDialog" />
                  </template>
                </el-input>
              </div>

              <el-input
                v-else-if="field.rawSchema?.['x-component'] === 'CodeEditor'"
                :model-value="formatDisplayValue(field)"
                type="textarea"
                :rows="3"
                readonly
                resize="none"
                class="param-code-preview"
                @click.stop="startParamEdit(index, fieldIndex)"
              />
              <span
                v-else
                class="param-value editable"
                @click.stop="startParamEdit(index, fieldIndex)"
              >
                {{ formatDisplayValue(field) }}
                <el-tag v-if="field.required" size="small" type="danger" style="margin-left: 4px">{{ t('node_block.required') }}</el-tag>
                <el-icon v-if="isSmartSelectorField(field)" class="selector-icon">
                  <ArrowDown />
                </el-icon>
                <el-icon v-else-if="field.rawSchema?.['x-component'] === 'DirectorySelect'" class="selector-icon">
                  <Folder />
                </el-icon>
                <el-icon v-else class="edit-icon">
                  <EditPen />
                </el-icon>
              </span>
            </div>
          </div>
        </div>

        <div class="node-outputs" v-if="node.outputs && node.outputs.length > 0">
          <div class="outputs-title">{{ t('node_block.output_fields') }}</div>
          <div class="output-items">
            <el-tag
              v-for="output in node.outputs"
              :key="output.name"
              size="small"
              type="success"
              class="output-tag"
            >
              {{ node.variable }}.{{ output.name }}
            </el-tag>
          </div>
        </div>

        <div v-if="node.status" class="node-status" :class="`status-${node.status}`">
          <el-icon v-if="node.status === 'running'"><Loading /></el-icon>
          <el-icon v-else-if="node.status === 'completed'"><CircleCheck /></el-icon>
          <el-icon v-else-if="node.status === 'error'"><CircleClose /></el-icon>
          <span>{{ getStatusText(node.status) }}</span>
          <span v-if="node.progress !== undefined && node.status === 'running'">
            {{ node.progress }}%
          </span>
        </div>
      </div>

      <div class="add-node-block" @click="showAddNodeDialog">
        <el-icon><Plus /></el-icon>
        <span>{{ t('node_block.add_node') }}</span>
      </div>
    </div>

    <el-dialog
      v-model="addNodeDialogVisible"
      :title="t('node_block.add_node')"
      width="600px"
    >
      <el-select
        v-model="selectedNodeType"
        :placeholder="t('node_block.select_node_type')"
        filterable
        style="width: 100%; margin-bottom: 16px"
      >
        <el-option-group
          v-for="(nodeList, category) in nodeTypesByCategory"
          :key="category"
          :label="category"
        >
          <el-option
            v-for="nodeType in nodeList"
            :key="nodeType.type"
            :label="`${getLocalizedNodeLabel(nodeType)} (${nodeType.type})`"
            :value="nodeType.type"
          >
            <div style="display: flex; flex-direction: column">
              <span>{{ getLocalizedNodeLabel(nodeType) }}</span>
              <span style="font-size: 12px; color: #909399">{{ getLocalizedNodeDescription(nodeType) }}</span>
            </div>
          </el-option>
        </el-option-group>
      </el-select>

      <el-input
        v-model="newNodeVariable"
        :placeholder="t('node_block.variable_placeholder')"
        style="width: 100%"
      />

      <template #footer>
        <el-button @click="addNodeDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="addNode">{{ t('common.add') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, Loading, CircleCheck, CircleClose, EditPen, Folder, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getContentModels } from '@/api/cards'
import { storeToRefs } from 'pinia'
import { useProjectListStore } from '@/stores/useProjectListStore'
import { useLLMConfigStore } from '@/stores/useLLMConfigStore'
import { usePromptStore } from '@/stores/usePromptStore'
import { useCardStore } from '@/stores/useCardStore'
import { ParameterFormatter } from '@/utils/parameterFormatter'
import { applyWorkflowPatch } from '@/api/workflowAgent'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isRunning: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: Number,
    default: null
  },
  revision: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'node-selected', 'revision-changed'])
const { t } = useI18n()

const projectListStore = useProjectListStore()
const llmConfigStore = useLLMConfigStore()
const promptStore = usePromptStore()
const cardStore = useCardStore()

const { projects: projectList } = storeToRefs(projectListStore)
const { llmConfigs: llmConfigList } = storeToRefs(llmConfigStore)
const { prompts: promptList } = storeToRefs(promptStore)
const { cardTypes: cardTypeList } = storeToRefs(cardStore)

const nodes = ref([])
const selectedIndex = ref(-1)
const addNodeDialogVisible = ref(false)
const selectedNodeType = ref('')
const newNodeVariable = ref('')
const nodeTypes = ref([])
const editingParam = ref(null)
const paramInputRef = ref(null)
const editingVariable = ref(null)
const variableInputRef = ref(null)
const variableList = ref([])
const fileDialogVisible = ref(false)
const builtinResponseModels = ref([])
const isInternalUpdate = ref(false)
const parseWatchSeq = ref(0)
const revisionRef = ref(props.revision || '')

watch(() => props.revision, value => {
  revisionRef.value = value || ''
})

const nodeTypesByCategory = computed(() => {
  const grouped = {}
  nodeTypes.value.forEach(nodeType => {
    if (!grouped[nodeType.category]) {
      grouped[nodeType.category] = []
    }
    grouped[nodeType.category].push(nodeType)
  })
  return grouped
})


function nodeLocaleKey(nodeType, field) {
  return `workflow_nodes.${String(nodeType || '').replace(/\./g, '_')}.${field}`
}

function getLocalizedNodeLabel(nodeType) {
  const key = nodeLocaleKey(nodeType.type, 'label')
  const value = String(t(key))
  return value && value !== key ? value : (nodeType.label || nodeType.type)
}

function getLocalizedNodeDescription(nodeType) {
  const key = nodeLocaleKey(nodeType.type, 'description')
  const value = String(t(key))
  return value && value !== key ? value : (nodeType.description || '')
}

function getLocalizedValueLabel(value) {
  const raw = String(value || '')
  if (!raw) return raw
  const normalized = raw.replace(/^['"]|['"]$/g, '')
  const key = `node_block.value_labels.${normalized}`
  const translated = String(t(key))
  if (!translated || translated === key) return raw
  return raw === normalized ? translated : raw.replace(normalized, translated)
}

function humanizeFieldName(fieldName) {
  return String(fieldName || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase())
}

function getLocalizedFieldLabel(fieldName, fallback) {
  const translated = String(t(`node_block.field_labels.${fieldName}`))
  return translated && translated !== `node_block.field_labels.${fieldName}` ? translated : (fallback || humanizeFieldName(fieldName))
}

async function parseCodeToNodes(code) {
  if (!code || !code.trim()) return []

  try {
    const response = await request.post('/workflows/parse', { code }, '/api')

    if (!response.success || !response.statements) {
      const errorMsg = response.errors?.join('; ') || response.error || t('common.unknown_error')
      console.error('[NodeBlockEditor] workflow parse failed', {
        error: errorMsg,
        errors: response.errors,
        debug: response.debug,
        codePreview: String(code || '').split('\n').slice(0, 12).join('\n'),
      })
      throw new Error(errorMsg)
    }


    const parsedNodes = []

    for (let i = 0; i < response.statements.length; i++) {
      const stmt = response.statements[i]


      if (stmt.node_type && stmt.node_type !== 'expression' && stmt.node_type !== '_wait') {
        const parts = stmt.node_type.split('.')
        const category = parts[0]
        const method = parts.slice(1).join('.')

        const node = {
          variable: stmt.variable,
          category: category,
          method: method,
          nodeType: stmt.node_type,
          description: stmt.description || '',
          params: stmt.config || {},
          code: stmt.code,
          outputs: [],
          collapsed: false,
          disabled: stmt.disabled || false,
          isAsync: stmt.is_async || false
        }

        await fetchNodeOutputs(node)
        parsedNodes.push(node)
      } else {
        parsedNodes.push({
          variable: stmt.variable,
          category: 'Raw',
          method: 'Code',
          nodeType: stmt.node_type || 'Raw.Code',
          description: stmt.description || '',
          params: stmt.config || {},
          code: stmt.code,
          outputs: [],
          collapsed: false,
          disabled: stmt.disabled || false,
          isAsync: stmt.is_async || false
        })
      }
    }
    return parsedNodes
  } catch (error) {
    throw error
  }
}

async function fetchNodeOutputs(node) {
  try {
    const response = await request.get(`/nodes/${node.nodeType}/metadata`, undefined, '/api', {
      showLoading: false
    })
    node.outputs = response.outputs || []

    const schema = response.input_schema?.properties || {}
    const hiddenFields = ['debug', 'debug_mode', 'verbose', 'log_level']

    const schemaFields = Object.entries(schema)
      .filter(([fieldName]) => !hiddenFields.includes(fieldName))
      .map(([fieldName, fieldDef]) => {
        let rawValue = node.params?.[fieldName]

        let formattedValue = ''

        if (rawValue !== undefined && rawValue !== null && rawValue !== '') {
          const fieldType = resolveFieldType(fieldDef)

          console.log(`[fetchNodeOutputs] processing field ${fieldName}:`, {
            fieldType,
            rawValue,
            rawValueType: typeof rawValue,
            isObject: typeof rawValue === 'object',
            isArray: Array.isArray(rawValue)
          })

          try {
            formattedValue = ParameterFormatter.format({
              type: fieldType,
              value: rawValue
            })

            console.log(`[fetchNodeOutputs] format succeeded ${fieldName}:`, {
              formattedValue,
              formattedType: typeof formattedValue
            })

            if (typeof formattedValue !== 'string') {
              formattedValue = JSON.stringify(formattedValue)
            }
          } catch (e) {
            if (typeof rawValue === 'object' && rawValue !== null) {
              formattedValue = JSON.stringify(rawValue)
            } else {
              formattedValue = String(rawValue)
            }
          }
        }

        return {
          name: fieldName,
          label: getLocalizedFieldLabel(fieldName, fieldDef.description),
          type: resolveFieldType(fieldDef),
          required: fieldDef.required || false,
          default: fieldDef.default,
          value: formattedValue,
          rawSchema: fieldDef
        }
      })

    const schemaFieldNames = new Set(Object.keys(schema))
    const extraFields = Object.entries(node.params || {})
      .filter(([fieldName]) => !schemaFieldNames.has(fieldName) && !hiddenFields.includes(fieldName))
      .map(([fieldName, rawValue]) => {
        let fieldType = 'string'
        if (typeof rawValue === 'number') {
          fieldType = Number.isInteger(rawValue) ? 'integer' : 'number'
        } else if (typeof rawValue === 'boolean') {
          fieldType = 'boolean'
        } else if (Array.isArray(rawValue)) {
          fieldType = 'array'
        } else if (typeof rawValue === 'object' && rawValue !== null) {
          fieldType = 'object'
        }

        console.log(`[fetchNodeOutputs] processing extra field ${fieldName}:`, {
          fieldType,
          rawValue,
          rawValueType: typeof rawValue
        })

        let formattedValue = ''
        try {
          formattedValue = ParameterFormatter.format({
            type: fieldType,
            value: rawValue
          })

          console.log(`[fetchNodeOutputs] extra field format succeeded ${fieldName}:`, {
            formattedValue,
            formattedType: typeof formattedValue
          })

          if (typeof formattedValue !== 'string') {
            formattedValue = JSON.stringify(formattedValue)
          }
        } catch (e) {
          if (typeof rawValue === 'object' && rawValue !== null) {
            formattedValue = JSON.stringify(rawValue)
          } else {
            formattedValue = String(rawValue)
          }
        }

        return {
          name: fieldName,
          label: getLocalizedFieldLabel(fieldName, fieldName),
          type: fieldType,
          required: false,
          default: undefined,
          value: formattedValue,
          rawSchema: null
        }
      })

    node.fields = [...schemaFields, ...extraFields]

  } catch (error) {
    node.outputs = []
    node.fields = []
  }
}

function parseParams(paramsStr) {
  const params = {}
  if (!paramsStr.trim()) return params

  const paramRegex = /(\w+)\s*=\s*([^,]+)/g
  let match

  while ((match = paramRegex.exec(paramsStr)) !== null) {
    const [, key, value] = match
    params[key] = value.trim().replace(/^["']|["']$/g, '')
  }

  return params
}

function buildNodeBlockCode(node, idx = -1) {
  if (!node?.variable || !node?.nodeType) {
    return ''
  }

  const paramParts = (node.fields || [])
    .filter(f => f.value !== undefined && f.value !== null && f.value !== '')
    .map(f => {
      let paramValue = f.value

      if (typeof paramValue === 'object' && paramValue !== null) {
        try {
          paramValue = ParameterFormatter.format({
            type: f.type || 'object',
            value: paramValue
          })
        } catch {
          paramValue = JSON.stringify(paramValue)
        }
      }

      const paramStr = String(paramValue)
      if (paramStr === '[object Object]') {
        try {
          paramValue = JSON.stringify(f.value)
        } catch {
          paramValue = '""'
        }
      }

      return `${f.name}=${paramValue}`
    })

  const callExpr = paramParts.length
    ? `${node.variable} = ${node.nodeType}(\n${paramParts.map(p => `    ${p}`).join(',\n')}\n)`
    : `${node.variable} = ${node.nodeType}()`

  const metaParts = []
  if (node.isAsync) metaParts.push('async=true')
  if (node.disabled) metaParts.push('disabled=true')
  if (node.description && String(node.description).trim()) {
    metaParts.push(`description=${JSON.stringify(String(node.description))}`)
  }

  const metaLine = `#@node(${metaParts.join(', ')})`
  return `${metaLine}
${callExpr}
#</node>`
}

function escapeRegex(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function parseNodeBlocksFromCode(code) {
  const normalized = String(code || '').replace(/\r\n/g, '\n')
  const lines = normalized.split('\n')
  const blocks = []

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index]
    if (!line || !line.trim().startsWith('#@node')) continue

    const startLine = index
    let endLine = -1
    let variable = null

    for (let cursor = index + 1; cursor < lines.length; cursor++) {
      const current = lines[cursor]
      if (!variable) {
        const assignMatch = current.match(/^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)
        if (assignMatch) {
          variable = assignMatch[1]
        }
      }

      if (current.trim() === '#</node>') {
        endLine = cursor
        break
      }
    }

    if (endLine >= 0) {
      blocks.push({
        variable,
        startLine,
        endLine,
      })
      index = endLine
    }
  }

  return { lines, blocks }
}

function normalizeEditorCode(code) {
  return String(code || '')
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/\s+$/, '')
}

function updateSingleNodeCode(node) {
  const currentCode = props.modelValue || ''
  const nodeBlock = buildNodeBlockCode(node)
  if (!nodeBlock) {
    return currentCode
  }

  if (!currentCode.trim()) {
    return normalizeEditorCode(nodesToCode())
  }

  const { lines, blocks } = parseNodeBlocksFromCode(currentCode)
  const target = blocks.find(block => block.variable === node.variable)
  if (!target) {
    return currentCode
  }

  const newBlockLines = String(nodeBlock).replace(/\r\n/g, '\n').split('\n')
  const newLines = [
    ...lines.slice(0, target.startLine),
    ...newBlockLines,
    ...lines.slice(target.endLine + 1),
  ]

  return normalizeEditorCode(newLines.join('\n'))
}

function removeSingleNodeCode(nodeVariable) {
  const currentCode = props.modelValue || ''
  if (!nodeVariable) {
    return currentCode
  }

  if (!currentCode.trim()) {
    return ''
  }

  const { lines, blocks } = parseNodeBlocksFromCode(currentCode)
  const target = blocks.find(block => block.variable === nodeVariable)
  if (!target) {
    return currentCode
  }

  const newLines = [
    ...lines.slice(0, target.startLine),
    ...lines.slice(target.endLine + 1),
  ]

  return normalizeEditorCode(newLines.join('\n'))
}

function appendSingleNodeCode(node) {
  const currentCode = props.modelValue || ''
  const nodeBlock = buildNodeBlockCode(node)
  if (!nodeBlock) return currentCode || ''

  if (!currentCode.trim()) {
    return normalizeEditorCode(nodeBlock)
  }

  const trimmedEnd = currentCode.replace(/\s+$/, '')
  return normalizeEditorCode(`${trimmedEnd}\n\n${nodeBlock}`)
}

function nodesToCode() {
  const nodeBlocks = nodes.value.map((node, idx) => buildNodeBlockCode(node, idx)).filter(code => code.trim() !== '')

  const result = nodeBlocks.join('\n\n')
  return result
}

function emitCodeUpdate(newCode, options = { internal: true }) {
  const normalized = typeof newCode === 'string' ? newCode : ''
  const current = typeof props.modelValue === 'string' ? props.modelValue : ''
  if (normalized === current) {
    return false
  }

  if (options.internal !== false) {
    isInternalUpdate.value = true
  }

  emit('update:modelValue', normalized)
  return true
}

async function applyCodeUpdateSafely(newCode, options = {}) {
  const normalized = typeof newCode === 'string' ? newCode : ''
  const current = typeof props.modelValue === 'string' ? props.modelValue : ''
  if (normalized === current) {
    return true
  }

  try {
    if (props.workflowId && revisionRef.value) {
      const result = await applyWorkflowPatch(props.workflowId, {
        base_revision: revisionRef.value,
        patch_ops: [
          {
            op: 'replace_code',
            new_code: normalized,
            reason: 'node_block_editor_safe_apply',
          },
        ],
        dry_run: false,
      })

      const finalCode = typeof result?.new_code === 'string' && result.new_code.length
        ? result.new_code
        : normalized

      if (!result?.success) {
        if (result?.error === 'validate_failed') {
          const parsedNodes = await parseCodeToNodes(finalCode)
          nodes.value = parsedNodes
          emitCodeUpdate(finalCode)
          if (!options.silent) {
            ElMessage.warning(t('node_block.messages.validation_failed_local_only'))
          }
          return true
        }

        throw new Error(result?.error || t('node_block.messages.backend_patch_failed'))
      }

      const parsedNodes = await parseCodeToNodes(finalCode)
      nodes.value = parsedNodes
      revisionRef.value = result.new_revision || revisionRef.value
      emit('revision-changed', revisionRef.value)
      emitCodeUpdate(finalCode)
      return true
    }

    const parsedNodes = await parseCodeToNodes(normalized)
    nodes.value = parsedNodes
    emitCodeUpdate(normalized)
    return true
  } catch (error) {
    if (!options.silent) {
      ElMessage.error(t('node_block.messages.code_update_failed', { error: error?.message || error }))
    }
    return false
  }
}

function selectNode(index) {
  selectedIndex.value = index
  emit('node-selected', nodes.value[index])
}

function deleteNode(index) {
  const removedNode = nodes.value[index]
  nodes.value.splice(index, 1)
  if (selectedIndex.value === index) {
    selectedIndex.value = -1
    emit('node-selected', null)
  } else if (selectedIndex.value > index) {
    selectedIndex.value--
  }

  emitCodeUpdate(removeSingleNodeCode(removedNode?.variable))
}

async function toggleNodeDisabled(index) {
  const node = nodes.value[index]
  const targetDisabledState = node.disabled
  const previousDisabledState = !targetDisabledState

  const applied = await applyCodeUpdateSafely(updateSingleNodeCode(node), { silent: true })
  if (!applied) {
    node.disabled = previousDisabledState
    ElMessage.error(t('node_block.messages.node_status_update_failed'))
    return
  }

  const message = targetDisabledState ? t('node_block.messages.node_disabled') : t('node_block.messages.node_enabled')
  ElMessage.success(message)
}

async function toggleAsync(index) {
  const node = nodes.value[index]
  const previousAsyncState = node.isAsync

  node.isAsync = !node.isAsync

  const targetAsyncState = node.isAsync

  const newCode = updateSingleNodeCode(node)

  const applied = await applyCodeUpdateSafely(newCode, { silent: true })
  if (!applied) {
    node.isAsync = previousAsyncState
    ElMessage.error(t('node_block.messages.async_status_update_failed'))
    return
  }

  const message = targetAsyncState ? t('node_block.messages.switched_to_async') : t('node_block.messages.switched_to_sync')
  ElMessage.success(message)
}

function showAddNodeDialog() {
  selectedNodeType.value = ''
  newNodeVariable.value = ''
  addNodeDialogVisible.value = true
}

async function addNode() {
  if (!selectedNodeType.value || !newNodeVariable.value) {
    ElMessage.warning(t('node_block.messages.select_type_and_variable'))
    return
  }

  try {
    const code = `#@node()
${newNodeVariable.value} = ${selectedNodeType.value}()
#</node>`


    const parsed = await parseCodeToNodes(code)

    if (parsed && parsed.length > 0) {

      nodes.value.push(parsed[0])

      const finalCode = appendSingleNodeCode(parsed[0])

      emitCodeUpdate(finalCode)
      selectedIndex.value = nodes.value.length - 1
      emit('node-selected', nodes.value[selectedIndex.value])
      ElMessage.success(t('node_block.messages.node_added'))
    } else {
      ElMessage.error(t('node_block.messages.node_add_failed_parse'))
    }
  } catch (error) {
    ElMessage.error(t('node_block.messages.node_add_failed', { error: error.message || error }))
  }

  addNodeDialogVisible.value = false
}

function startParamEdit(nodeIndex, fieldIndex) {
  const node = nodes.value[nodeIndex]
  const field = node.fields[fieldIndex]


  let editValue = field.value
  if (editValue === undefined || editValue === null) {
    editValue = field.default || (field.type === 'boolean' ? false : '')
  }

  console.log('[startParamEdit] raw value:', {
    fieldName: field.name,
    fieldType: field.type,
    editValue,
    isArray: Array.isArray(editValue),
    valueType: typeof editValue
  })

  if (field.type === 'boolean') {
    if (typeof editValue === 'string') {
      editValue = editValue === 'True' || editValue === 'true'
    }
  }
  else if (field.type === 'array') {
    if (typeof editValue === 'string') {
      if ((editValue.startsWith('"') && editValue.endsWith('"')) ||
          (editValue.startsWith("'") && editValue.endsWith("'"))) {
        editValue = editValue.substring(1, editValue.length - 1)
      }
    }

    let arrayItems = []
    if (Array.isArray(editValue)) {
      arrayItems = editValue.map(item => {
        const str = String(item)
        if ((str.startsWith('"') && str.endsWith('"')) || (str.startsWith("'") && str.endsWith("'"))) {
          return str.substring(1, str.length - 1)
        }
        return str
      })
    }
    else if (typeof editValue === 'string' && editValue.startsWith('[') && editValue.endsWith(']')) {
      try {
        const parsed = JSON.parse(editValue.replace(/'/g, '"'))
        arrayItems = parsed.map(item => {
          const str = String(item)
          if ((str.startsWith('"') && str.endsWith('"')) || (str.startsWith("'") && str.endsWith("'"))) {
            return str.substring(1, str.length - 1)
          }
          return str
        })
      } catch (e) {
        const content = editValue.substring(1, editValue.length - 1)
        arrayItems = content.split(',').map(s => {
          const trimmed = s.trim()
          if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
            return trimmed.substring(1, trimmed.length - 1)
          }
          return trimmed
        }).filter(item => item)
      }
    }
    else if (typeof editValue === 'string' && editValue.includes(',')) {
      arrayItems = editValue.split(',').map(s => s.trim()).filter(item => item)
    }
    else if (editValue) {
      arrayItems = [String(editValue)]
    }


    editValue = arrayItems
  }
  else if (typeof editValue === 'string' && field.type === 'string') {
    if ((editValue.startsWith('"') && editValue.endsWith('"')) ||
        (editValue.startsWith("'") && editValue.endsWith("'"))) {
      editValue = editValue.substring(1, editValue.length - 1)
    }
  }

  editingParam.value = {
    nodeIndex,
    fieldIndex,
    fieldName: field.name,
    fieldType: field.type,
    value: field.type === 'array' ? null : editValue,
    arrayItems: field.type === 'array' ? editValue : []
  }

}

function addArrayItem() {
  if (!editingParam.value || !editingParam.value.arrayItems) return
  editingParam.value.arrayItems.push('')
}

function removeArrayItem(index) {
  if (!editingParam.value || !editingParam.value.arrayItems) return
  editingParam.value.arrayItems.splice(index, 1)
}

async function saveParamEdit() {
  if (!editingParam.value) return

  const { nodeIndex, fieldIndex, fieldName, value, arrayItems } = editingParam.value
  const node = nodes.value[nodeIndex]

  if (!node || !node.fields || !node.fields[fieldIndex]) {
    ElMessage.error(t('node_block.messages.save_failed_invalid_node'))
    editingParam.value = null
    return
  }

  const field = node.fields[fieldIndex]
  const fieldType = field.type || editingParam.value.fieldType || 'string'
  const previousFieldValue = field.value

  console.log('[saveParamEdit] saving param:', {
    nodeIndex,
    fieldIndex,
    fieldName,
    fieldType,
    value,
    node: {
      variable: node.variable,
      nodeType: node.nodeType,
      fieldsCount: node.fields.length
    }
  })

  try {
    let finalValue = value
    if (fieldType === 'array' && arrayItems) {
      const filteredItems = arrayItems.filter(item => item && item.trim())
      finalValue = filteredItems
    }

    if (ParameterFormatter.isEmpty(finalValue)) {
      field.value = undefined

      const allCode = updateSingleNodeCode(node)
      const applied = await applyCodeUpdateSafely(allCode, { silent: true })
      if (!applied) {
        field.value = previousFieldValue
        ElMessage.error(t('node_block.messages.clear_param_failed'))
        editingParam.value = null
        return
      }
      ElMessage.success(t('node_block.messages.param_cleared'))

      editingParam.value = null
      return
    }

    const formattedValue = ParameterFormatter.format({
      type: fieldType,
      value: finalValue
    })


    if (String(formattedValue) === String(field.value ?? '')) {
      editingParam.value = null
      return
    }

    field.value = formattedValue

    nodes.value.forEach((n, idx) => {
      console.log(`  [${idx}] ${n.variable}: fields=`, n.fields?.map(f => `${f.name}=${f.value}`))
    })

    const allCode = updateSingleNodeCode(node)

    if (!allCode || allCode.trim() === '') {
      throw new Error(t('node_block.messages.generated_code_empty'))
    }

    const applied = await applyCodeUpdateSafely(allCode, { silent: true })
    if (!applied) {
      field.value = previousFieldValue
      ElMessage.error(t('node_block.messages.param_update_failed'))
      editingParam.value = null
      return
    }
    ElMessage.success(t('node_block.messages.param_updated'))

    editingParam.value = null
  } catch (error) {
    ElMessage.error(t('node_block.messages.save_failed_with_error', { error: error.message }))
    editingParam.value = null
  }
}


async function openFolderDialog() {
  try {
    const result = await window.electron.ipcRenderer.invoke('dialog:openDirectory')
    if (result && !result.canceled && result.filePaths.length > 0) {
      if (editingParam.value) {
        const path = result.filePaths[0]
        editingParam.value.value = path.replace(/\\/g, '\\\\')
        saveParamEdit()
      }
    }
  } catch (e) {
    console.error('Failed to open directory dialog:', e)
  }
}

function showAvailableParams(nodeIndex) {
  const node = nodes.value[nodeIndex]
  if (!node.fields || node.fields.length === 0) {
    ElMessage.info(t('node_block.messages.no_configurable_params'))
    return
  }

  node.fields.forEach(field => {
    if (field.required && !field.value) {
      field.value = field.default || ''
    }
  })

  emitCodeUpdate(updateSingleNodeCode(node))
}

function formatParamValue(value) {
  if (value === undefined || value === null || value === '') {
    return t('node_block.messages.not_set')
  }

  const strValue = String(value)

  if (strValue.length > 50) {
    return strValue.substring(0, 50) + '...'
  }

  return strValue
}

function getNodeCategoryColor(category) {
  const colors = {
    'Logic': 'primary',
    'Novel': 'success',
    'Card': 'warning',
    'AI': 'danger',
    'Prompt': 'info'
  }
  return colors[category] || 'info'
}

function getStatusText(status) {
  const texts = {
    'running': t('node_block.status.running'),
    'completed': t('node_block.status.completed'),
    'error': t('node_block.status.error')
  }
  return texts[status] || ''
}

async function loadNodeTypes() {
  try {
    const response = await request.get('/nodes/types', undefined, '/api', { showLoading: false })
    nodeTypes.value = response.node_types || []
  } catch (error) {
  }
}

watch(() => props.modelValue, async (newCode, oldCode) => {
  if (newCode === oldCode) {
    return
  }

  if (isInternalUpdate.value) {
    isInternalUpdate.value = false
    return
  }


  const requestSeq = ++parseWatchSeq.value

  try {
    const parsedNodes = await parseCodeToNodes(newCode)
    if (requestSeq !== parseWatchSeq.value) {
      return
    }
    nodes.value = parsedNodes
  } catch (error) {
    if (requestSeq !== parseWatchSeq.value) {
      return
    }
    if (oldCode !== undefined) {
      ElMessage.error(t('node_block.messages.code_parse_failed_with_error', { error: error.message || error }))
    }
  }
}, { immediate: true })

function updateVariableList() {
  const vars = []
  nodes.value.forEach(node => {
     if (node.variable) {
        vars.push({
           value: node.variable,
           label: node.variable,
           type: 'variable'
        })
     }
  })
  variableList.value = vars
}

function isSmartSelectorField(field) {
  if (!field || !field.rawSchema) return false
  const xComponent = field.rawSchema['x-component']
  return ['ProjectSelect', 'LLMSelect', 'PromptSelect', 'CardTypeSelect', 'ResponseModelSelect', 'ToolMultiSelect'].includes(xComponent)
}

function getProjectOptionValue(field, project) {
  if (field?.name === 'project_name') {
    return project?.name ?? ''
  }
  return project?.id
}

function getLlmOptionValue(field, llmConfig) {
  if (field?.name === 'llm_name') {
    return llmConfig?.display_name || llmConfig?.model_name || ''
  }
  return llmConfig?.id
}

function toggleNodeCollapse(index) {
  const node = nodes.value[index]
  node.collapsed = !node.collapsed
}

function startVariableEdit(nodeIndex, currentVariable) {

  editingVariable.value = {
    nodeIndex,
    value: currentVariable,
    originalValue: currentVariable
  }

  nextTick(() => {
    if (variableInputRef.value) {
      variableInputRef.value.focus()
      variableInputRef.value.select()
    }
  })
}

async function saveVariableEdit() {
  console.log('[saveVariableEdit] editingVariable:', editingVariable.value)

  if (!editingVariable.value) {
    return
  }

  const { nodeIndex, value, originalValue } = editingVariable.value
  const newVariable = value.trim()


  if (!newVariable) {
    ElMessage.error(t('node_block.messages.variable_name_required'))
    editingVariable.value = null
    return
  }

  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(newVariable)) {
    ElMessage.error(t('node_block.messages.invalid_variable_name'))
    editingVariable.value = null
    return
  }

  const isDuplicate = nodes.value.some((n, idx) => idx !== nodeIndex && n.variable === newVariable)
  if (isDuplicate) {
    ElMessage.error(t('node_block.messages.variable_name_used', { name: newVariable }))
    editingVariable.value = null
    return
  }

  if (newVariable === originalValue) {
    editingVariable.value = null
    return
  }


  const allCode = props.modelValue || nodesToCode()

  try {
    console.log('[saveVariableEdit] request params:', {
      code: allCode,
      old_name: originalValue,
      new_name: newVariable
    })

    const response = await request.post('/workflows/rename-variable', {
      code: allCode,
      old_name: originalValue,
      new_name: newVariable
    }, '/api')


    if (response.success && response.new_code) {

      emitCodeUpdate(response.new_code)

      try {
        nodes.value = await parseCodeToNodes(response.new_code)
      } catch (error) {
      }

      ElMessage.success(t('node_block.messages.variable_renamed', { from: originalValue, to: newVariable }))
    } else {
      ElMessage.error(t('node_block.messages.rename_failed', { error: response.error || t('common.unknown_error') }))
    }
  } catch (error) {
    ElMessage.error(t('node_block.messages.rename_failed', { error: error.message || error }))
  }

  editingVariable.value = null
}

function cancelVariableEdit() {
  editingVariable.value = null
}

function formatDisplayValue(field) {
  if (ParameterFormatter.isEmpty(field.value)) {
    return getLocalizedValueLabel(field.default) || t('node_block.messages.not_set')
  }

  let displayValue = getLocalizedValueLabel(ParameterFormatter.parseDisplayValue(field.value))

  const xComponent = field.rawSchema?.['x-component']

  if (xComponent === 'ProjectSelect') {
    const projectId = parseInt(displayValue)
    const project = projectList.value.find(p => p.id === projectId)
    if (project) {
      displayValue = project.name
    }
  } else if (xComponent === 'LLMSelect') {
    const llmConfigId = parseInt(displayValue)
    const llmConfig = llmConfigList.value.find(cfg => cfg.id === llmConfigId)
    if (llmConfig) {
      displayValue = llmConfig.display_name || llmConfig.model_name || `LLM #${llmConfigId}`
    }
  } else if (xComponent === 'PromptSelect') {
    // Show prompt display name
    const promptId = parseInt(displayValue)
    const prompt = promptList.value.find(p => p.id === promptId)
    if (prompt) {
      displayValue = prompt.name
    }
  } else if (xComponent === 'CardTypeSelect' || xComponent === 'ResponseModelSelect') {
    const cardType = cardTypeList.value.find(ct => (ct.key || ct.name) === displayValue)
    if (cardType) {
      displayValue = cardType.name
    }
  }


  if (xComponent === 'CodeEditor' || xComponent === 'Textarea') {
    return displayValue
  }

  return displayValue.length > 50 ? displayValue.substring(0, 50) + '...' : displayValue
}

function resolveFieldType(fieldDef) {
  if (!fieldDef || typeof fieldDef !== 'object') {
    return 'string'
  }

  if (typeof fieldDef.type === 'string' && fieldDef.type.trim()) {
    return fieldDef.type
  }

  if (Array.isArray(fieldDef.type)) {
    const picked = fieldDef.type.find(t => typeof t === 'string' && t !== 'null')
    if (picked) return picked
  }

  if (Array.isArray(fieldDef.anyOf)) {
    const picked = fieldDef.anyOf
      .map(item => item?.type)
      .find(t => typeof t === 'string' && t !== 'null')
    if (picked) return picked
  }

  if (Array.isArray(fieldDef.oneOf)) {
    const picked = fieldDef.oneOf
      .map(item => item?.type)
      .find(t => typeof t === 'string' && t !== 'null')
    if (picked) return picked
  }

  return 'string'
}

onMounted(async () => {
  loadNodeTypes()

  try {
    await Promise.all([
      projectListStore.fetchProjects(),
      llmConfigStore.fetchLLMConfigs(),
      promptStore.fetchPrompts(),
      cardStore.fetchInitialData()
    ])

    try {
      builtinResponseModels.value = await getContentModels()
    } catch (e) {
      builtinResponseModels.value = [
        'OneSentence',
        'ChapterOutline',
        'VolumeOutline',
        'WorldBuilding',
        'WritingGuide',
        'ParagraphOverview',
        'BookStageChunkPlan',
        'BookStageFinalPlan'
      ]
    }

  } catch (error) {
    console.error(t('node_block.messages.load_data_failed'), error)
  }
})
</script>

<style scoped>
.node-block-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.node-blocks {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.node-block {
  margin-bottom: 12px;
  padding: 16px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.node-block:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 12px var(--el-box-shadow-light);
}

.node-block.is-selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.node-block.is-disabled {
  opacity: 0.5;
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-light);
  position: relative;
}

.node-block.is-disabled::before {
  content: t('node_block.messages.node_disabled');
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  background: var(--el-text-color-secondary);
  color: white;
  font-size: 12px;
  border-radius: 4px;
  z-index: 1;
}

.node-block.is-disabled:hover {
  border-color: var(--el-border-color);
  box-shadow: none;
}

.node-block.is-disabled .node-variable,
.node-block.is-disabled .node-type,
.node-block.is-disabled .param-label,
.node-block.is-disabled .param-value {
  color: var(--el-text-color-secondary);
}

.node-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-variable {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.node-type {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.node-description {
  margin: -4px 0 10px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.5;
  border-left: 3px solid var(--el-color-primary-light-5);
}

.node-actions {
  display: flex;
  gap: 4px;
}

.node-params {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  font-size: 13px;
  margin-bottom: 8px;
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.params-title {
  font-weight: 600;
  color: var(--el-text-color-regular);
  font-size: 12px;
  text-transform: uppercase;
}

.param-item {
  display: flex;
  gap: 8px;
}

.param-key {
  color: var(--el-text-color-secondary);
  min-width: 120px;
}


.param-value-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
}

.param-value {
  color: var(--el-text-color-primary);
  flex: 1;
  word-break: break-all;
}

.param-value.editable {
  cursor: text;
  border-bottom: 1px dashed transparent;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.param-value.editable:hover {
  background-color: var(--el-color-primary-light-9);
  border-bottom-color: var(--el-color-primary);
  padding-left: 4px;
  border-radius: 2px;
}

.edit-icon {
  display: none;
  font-size: 12px;
  color: var(--el-color-primary);
}

.param-value.editable:hover .edit-icon {
  display: inline-flex;
}

.code-expression-input :deep(.el-textarea__inner),
.param-code-preview :deep(.el-textarea__inner) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Monaco', 'Menlo', 'Courier New', monospace;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.param-code-preview {
  width: 100%;
}

.param-code-preview :deep(.el-textarea__inner) {
  cursor: text;
  background-color: var(--el-fill-color-lighter);
}

.param-code-preview:hover :deep(.el-textarea__inner) {
  border-color: var(--el-color-primary);
}

.add-param-hint {
  padding: 8px 0;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.add-param-hint .el-button {
  color: var(--el-color-primary);
}

.node-outputs {
  padding: 12px;
  background: var(--el-color-primary-light-9);
  border-radius: 4px;
  margin-top: 8px;
}

.outputs-title {
  font-weight: 600;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
  font-size: 12px;
  text-transform: uppercase;
}

.output-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.output-tag {
  font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
  cursor: pointer;
}

.output-tag:hover {
  opacity: 0.8;
}

.node-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
}

.status-running {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.status-completed {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.status-error {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

.add-node-block {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  background: var(--el-bg-color);
  border: 2px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all 0.3s;
}

.add-node-block:hover {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}
</style>
