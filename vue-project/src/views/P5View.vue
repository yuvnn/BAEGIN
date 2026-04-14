<template>
  <div id="p5" class="page">
    <div class="p2-head">
      <div class="pg-title">사내 비교문서 목록</div>
    </div>
    <div class="paper-list">
      <div class="empty-state" v-if="loading">불러오는 중...</div>
      <div class="empty-state" v-else-if="!reports.length">
        생성하기 버튼을 눌러 첫 사내 비교문서를 만들어보세요.
      </div>
      <div
        v-for="r in reports"
        :key="r.report_id"
        class="rcard"
        @click="store.viewSavedReport(r.report_id)"
      >
        <div class="pcard-main">
          <div class="pcard-title">{{ r.title }}</div>
          <div class="pcard-abs" style="margin-bottom:4px;">논문 ID: {{ r.paper_id || '-' }}</div>
          <div class="pcard-meta">
            <span class="rcard-date">{{ r.updated_at ? r.updated_at.slice(0, 16).replace('T', ' ') : '' }} 생성</span>
            <span :class="['rcard-status', r.status]">{{ r.status }}</span>
          </div>
        </div>
        <div class="rcard-badge">열기 →</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { store } from '../store.js'
import { getReportList } from '../api/reportService.js'

const reports = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try { reports.value = await getReportList() } catch {} finally { loading.value = false }
})
</script>
