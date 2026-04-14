<template>
  <div id="p3" class="page" style="height:calc(100vh - 52px);">
    <div class="p3-inner">
      <div class="bc">
        <span @click="store.go('p1')">홈</span>
        <span class="sep">›</span>
        <span @click="store.go('p2')">논문리스트</span>
        <span class="sep">›</span>
        <span style="color:var(--t1)">{{ bcTitle }}</span>
      </div>
      <div class="dh">
        <div class="dh-title">{{ p.title }}</div>
        <div class="dh-row">
          <span class="dh-author">{{ p.authors }}</span>
          <span class="dh-sub">{{ p.date }}</span>
          <span class="dh-sub">조회 {{ p.views?.toLocaleString() }}</span>
        </div>
        <div class="dh-tags">
          <span class="dh-cat-badge" :style="catBadgeStyle">{{ p.cat }}</span>
        </div>
      </div>
      <div class="dbody">
        <div class="d-orig">
          <div class="sec-head" style="display:flex;align-items:center;justify-content:space-between;">
            <span>원본</span>
            <a v-if="p.pdf_url || p.paper_url"
               :href="p.pdf_url || p.paper_url"
               target="_blank"
               rel="noopener"
               style="font-size:11px;color:var(--t3);text-decoration:none;padding-right:4px;">
              논문 원문 ↗
            </a>
          </div>
          <div class="sec-body" v-html="origHtml"></div>
        </div>
        <div class="d-right">
          <div class="d-summ">
            <div class="sec-head">요약본</div>
            <div class="sec-body" v-html="summHtml"></div>
          </div>
          <div class="d-rel">
            <div class="sec-head" style="padding:11px 14px;">관련된 사내 문서</div>
            <template v-if="relDocs.length">
              <div v-for="d in relDocs" :key="d.internal_doc_id" class="rel-item-wrap">
                <div class="rel-item-left">
                  <div class="rel-dot"></div>
                  <span>{{ d.title }}</span>
                </div>
                <button class="btn-gen"
                  :disabled="generating === d.internal_doc_id"
                  @click="generateReport(d)">
                  {{ generating === d.internal_doc_id ? '생성 중...' : '생성하기' }}
                </button>
              </div>
            </template>
            <div v-else style="padding:11px 14px;font-size:12px;color:var(--t3)">관련 문서 없음</div>
          </div>
        </div>
      </div>
      <div class="banner" v-if="!relDocs.length">
        <div class="banner-txt"><strong>관련 사내 문서가 없습니다.</strong> 이 논문을 바탕으로 사내 문서를 만들겠습니까?</div>
        <button class="btn-mk" @click="store.go('p4')">만들겠습니다</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { store } from '../store.js'
import { TAG_C } from '../data/papers.js'
import { CL } from '../data/vizData.js'
import { fmt, fmtMd } from '../utils/format.js'
import { fetchPaperById, fetchPaperRelates } from '../api/paperService.js'
import { startReportGeneration, getInternalDocText } from '../api/reportService.js'

const p = computed(() => store.curPaper)
const bcTitle = computed(() => { const t = p.value.title; return t.length > 45 ? t.slice(0, 45) + '…' : t })

const origContent = ref('')
const relDocs = ref([])
const generating = ref(null)

const origHtml = computed(() => fmt(origContent.value || p.value.orig || ''))
const summHtml = computed(() => fmtMd(p.value.summ || ''))

const clColorMap = Object.fromEntries(CL.map(c => [c.name, { color: c.color, glow: c.glow }]))
const catBadgeStyle = computed(() => {
  const c = clColorMap[p.value.cat]
  if (!c) return {}
  return {
    background: c.glow,
    color: c.color,
    border: `1px solid ${c.color}55`,
  }
})

// v-show로 항상 마운트되어 있으므로 onMounted 대신 currentPage watch 사용
watch(
  () => store.currentPage,
  async (page) => {
    if (page !== 'p3') return
    const paperId = p.value.id || p.value.paper_id
    // 정적 PAPERS 더미 데이터(숫자 id)는 API 호출 스킵
    if (!paperId || typeof paperId === 'number') return

    origContent.value = ''
    relDocs.value = []

    // 1) 원본 abstract 로드
    if (!p.value.orig) {
      try {
        const detail = await fetchPaperById(paperId)
        origContent.value = detail.abstract || detail.md_summary || ''
      } catch {}
    }

    // 2) 관련 사내문서 동적 로드
    try {
      const result = await fetchPaperRelates(paperId)
      const relates = result.relates || []
      relDocs.value = await Promise.all(
        relates.map(async (r) => {
          try {
            const docInfo = await getInternalDocText(r.internal_doc_id)
            return { internal_doc_id: r.internal_doc_id, title: docInfo.title, reason: r.reason }
          } catch {
            return { internal_doc_id: r.internal_doc_id, title: r.internal_doc_id, reason: r.reason }
          }
        })
      )
    } catch {}
  },
  { immediate: true }
)

async function generateReport(doc) {
  if (generating.value) return
  generating.value = doc.internal_doc_id
  try {
    const accepted = await startReportGeneration({
      paper_id: p.value.id || p.value.paper_id,
      internal_doc_id: doc.internal_doc_id,
    })
    store.pendingStreamReportId = accepted.report_id
    store.go('p4')
  } catch (e) {
    console.error('[generateReport] failed:', e)
  } finally {
    generating.value = null
  }
}
</script>
