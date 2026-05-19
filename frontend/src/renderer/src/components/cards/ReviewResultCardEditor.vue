<template>
  <div class="review-result-card-editor">
    <div class="review-header">
      <div class="review-header-main">
        <div class="review-title-block">
          <h2 class="review-title">{{ card.title }}</h2>
          <div class="review-meta">
            <el-tag :type="verdictTagType" effect="dark" size="small">{{ verdictLabel }}</el-tag>
            <el-tag v-if="reviewProfile" type="info" effect="plain" size="small">{{ reviewProfile }}</el-tag>
            <el-tag v-if="targetField" type="info" effect="plain" size="small">{{ targetField }}</el-tag>
          </div>
        </div>
        <el-button size="small" plain type="primary" @click="jumpToTarget">{{ t('reviewResultCard.jumpToTarget') }}</el-button>
      </div>
      <div class="review-target">
        {{ t('reviewResultCard.target') }}：{{ targetTitle || t('reviewResultCard.unnamedTarget') }}
      </div>
    </div>

    <el-alert
      v-if="summaryText"
      :title="summaryText"
      :type="summaryAlertType"
      show-icon
      :closable="false"
      class="review-summary"
    />

    <div class="review-section" v-if="normalizedIssues.length">
      <div class="section-header">
        <span>{{ t('reviewResultCard.issues') }}</span>
        <el-tag size="small" type="danger">{{ normalizedIssues.length }}</el-tag>
      </div>
      <el-timeline>
        <el-timeline-item
          v-for="(issue, index) in normalizedIssues"
          :key="`${issue.id || index}`"
          :type="issueTimelineType(issue.severity)"
          :timestamp="issue.category || ''"
        >
          <div class="issue-item">
            <div class="issue-title-row">
              <span class="issue-title">{{ issue.title }}</span>
              <el-tag size="small" effect="plain" :type="issueTagType(issue.severity)">{{ severityLabel(issue.severity) }}</el-tag>
            </div>
            <p class="issue-description">{{ issue.description }}</p>
            <p v-if="issue.suggestion" class="issue-suggestion">{{ t('reviewResultCard.suggestion') }}：{{ issue.suggestion }}</p>
            <p v-if="issue.evidence" class="issue-evidence">{{ t('reviewResultCard.evidence') }}：{{ issue.evidence }}</p>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <div class="review-section" v-if="followUps.length">
      <div class="section-header">
        <span>{{ t('reviewResultCard.followUps') }}</span>
        <el-tag size="small" type="warning">{{ followUps.length }}</el-tag>
      </div>
      <ul class="simple-list">
        <li v-for="(item, index) in followUps" :key="`follow-up-${index}`">{{ item }}</li>
      </ul>
    </div>

    <div class="review-section" v-if="strengths.length">
      <div class="section-header">
        <span>{{ t('reviewResultCard.strengths') }}</span>
        <el-tag size="small" type="success">{{ strengths.length }}</el-tag>
      </div>
      <ul class="simple-list">
        <li v-for="(item, index) in strengths" :key="`strength-${index}`">{{ item }}</li>
      </ul>
    </div>

    <div class="review-section" v-if="rawOutput">
      <div class="section-header">
        <span>{{ t('reviewResultCard.rawOutput') }}</span>
      </div>
      <pre class="raw-output">{{ rawOutput }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useCardStore } from '@renderer/stores/useCardStore'
import type { CardRead } from '@renderer/api/cards'

const props = defineProps<{
  card: CardRead
}>()

const { t } = useI18n()
const cardStore = useCardStore()

const payload = computed<any>(() => props.card?.content || {})
const targetId = computed<number | null>(() => payload.value?.target_card_id ?? null)
const targetField = computed<string>(() => payload.value?.target_field || '')
const targetTitle = computed<string>(() => payload.value?.target_card_title || '')
const reviewProfile = computed<string>(() => payload.value?.review_profile || '')
const rawOutput = computed<string>(() => payload.value?.raw_output || '')
const followUps = computed<string[]>(() => Array.isArray(payload.value?.follow_ups) ? payload.value.follow_ups : [])
const strengths = computed<string[]>(() => Array.isArray(payload.value?.strengths) ? payload.value.strengths : [])
const normalizedIssues = computed<any[]>(() => Array.isArray(payload.value?.issues) ? payload.value.issues : [])
const summaryText = computed<string>(() => payload.value?.summary || '')
const verdict = computed<string>(() => payload.value?.verdict || 'needs_revision')

const summaryAlertType = computed(() => {
  switch (verdict.value) {
    case 'pass': return 'success'
    case 'warning': return 'warning'
    case 'fail': return 'error'
    default: return 'info'
  }
})

const verdictTagType = computed(() => {
  switch (verdict.value) {
    case 'pass': return 'success'
    case 'warning': return 'warning'
    case 'fail': return 'danger'
    default: return 'info'
  }
})

const verdictLabel = computed(() => {
  switch (verdict.value) {
    case 'pass': return t('reviewResultCard.verdict.pass')
    case 'warning': return t('reviewResultCard.verdict.warning')
    case 'fail': return t('reviewResultCard.verdict.fail')
    default: return t('reviewResultCard.verdict.needsRevision')
  }
})

function issueTagType(severity?: string) {
  switch (severity) {
    case 'critical': return 'danger'
    case 'major': return 'warning'
    case 'minor': return 'info'
    default: return 'info'
  }
}

function issueTimelineType(severity?: string) {
  switch (severity) {
    case 'critical': return 'danger'
    case 'major': return 'warning'
    case 'minor': return 'primary'
    default: return 'info'
  }
}

function severityLabel(severity?: string) {
  switch (severity) {
    case 'critical': return t('reviewResultCard.severity.critical')
    case 'major': return t('reviewResultCard.severity.major')
    case 'minor': return t('reviewResultCard.severity.minor')
    default: return t('reviewResultCard.severity.info')
  }
}

function jumpToTarget() {
  if (!targetId.value) {
    ElMessage.warning(t('reviewResultCard.noTarget'))
    return
  }
  const card = cardStore.cards.find((item) => item.id === targetId.value)
  if (!card) {
    ElMessage.warning(t('reviewResultCard.targetNotFound'))
    return
  }
  window.dispatchEvent(new CustomEvent('nf:open-card', { detail: { cardId: card.id } }))
}
</script>

<style scoped>
.review-result-card-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.review-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.review-header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.review-title-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.review-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
.review-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.review-target {
  color: var(--el-text-color-secondary);
}
.review-summary {
  white-space: pre-wrap;
}
.review-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.issue-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.issue-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.issue-title {
  font-weight: 600;
}
.issue-description,
.issue-suggestion,
.issue-evidence {
  margin: 0;
  white-space: pre-wrap;
}
.simple-list {
  margin: 0;
  padding-left: 18px;
}
.raw-output {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  overflow: auto;
  white-space: pre-wrap;
}
</style>
