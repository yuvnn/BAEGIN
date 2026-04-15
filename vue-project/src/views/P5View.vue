<template>
  <div id="p5" class="page">
    <div class="p2-head">
      <div class="pg-title">사내 비교문서 목록</div>
      <div class="fl-tags" v-if="categories.length > 1">
        <button v-for="cat in categories" :key="cat"
          class="ftag" :class="{ on: filterCat === cat }"
          @click="filterCat = cat">{{ cat }}</button>
      </div>
    </div>
    <div class="paper-list">
      <div class="empty-state" v-if="loading">불러오는 중...</div>
      <div class="empty-state" v-else-if="!reports.length">
        생성하기 버튼을 눌러 첫 사내 비교문서를 만들어보세요.
      </div>
      <div
        v-for="r in pagedReports"
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
    <div class="pg-bar" v-if="totalPages > 1">
      <button class="pg-btn" :disabled="currentPage === 1" @click="currentPage--">‹</button>
      <button v-for="n in pageNumbers" :key="n"
        class="pg-btn" :class="{ on: n === currentPage }"
        @click="currentPage = n">{{ n }}</button>
      <button class="pg-btn" :disabled="currentPage === totalPages" @click="currentPage++">›</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { store } from '../store.js'
import { getReportList } from '../api/reportService.js'

const reports = ref([])
const loading = ref(false)

const PAGE_SIZE = 10
const currentPage = ref(1)
const filterCat = ref('전체')

const categories = computed(() => {
  const cats = new Set(reports.value.map(r => r.category).filter(Boolean))
  return ['전체', ...cats]
})
const filteredReports = computed(() =>
  filterCat.value === '전체' ? reports.value
    : reports.value.filter(r => r.category === filterCat.value)
)
const totalPages = computed(() => Math.ceil(filteredReports.value.length / PAGE_SIZE))
const pagedReports = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredReports.value.slice(start, start + PAGE_SIZE)
})
const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  const s = Math.max(1, cur - 2)
  const e = Math.min(total, s + 4)
  return Array.from({ length: e - s + 1 }, (_, i) => s + i)
})

watch(filterCat, () => { currentPage.value = 1 })

onMounted(async () => {
  loading.value = true
  try { reports.value = await getReportList() } catch {} finally { loading.value = false }
})
</script>

<style scoped>
.fl-tags { display: flex; flex-wrap: wrap; gap: 6px; padding: 0 24px 12px; }
.ftag {
  padding: 4px 14px; border-radius: 20px;
  border: 1px solid var(--border); background: transparent;
  color: var(--t2); cursor: pointer; font-size: 12px;
}
.ftag.on { background: var(--teal); color: #fff; border-color: var(--teal); }
.pg-bar {
  display: flex; align-items: center; justify-content: center;
  gap: 4px; padding: 16px 0 8px;
}
.pg-btn {
  min-width: 32px; height: 32px; border-radius: 8px;
  border: 1px solid var(--border); background: transparent;
  color: var(--t2); cursor: pointer; font-size: 13px;
  display: flex; align-items: center; justify-content: center;
}
.pg-btn.on { background: var(--teal); color: #fff; border-color: var(--teal); }
.pg-btn:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
