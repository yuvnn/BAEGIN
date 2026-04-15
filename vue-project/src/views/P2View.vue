<template>
  <div id="p2" class="page">
    <div class="p2-head">
      <div class="pg-title">논문 리스트</div>
      
      <div class="fl">
        <div class="fl-label">카테고리 필터</div>
        <div class="fl-tags">
          <button
            v-for="cat in CATS"
            :key="cat"
            class="ftag"
            :class="{ on: store.curCat === cat }"
            @click="setCat(cat)"
          >{{ cat }}</button>
        </div>
      </div>

      <div class="fl-row">
        <div style="display:flex;align-items:center;gap:8px;flex:1;">
          <span style="font-size:12px;color:var(--t3);">날짜 필터</span>
          <input type="date" class="date-in" v-model="dateFrom" />
          <span style="font-size:12px;color:var(--t3);">~</span>
          <input type="date" class="date-in" v-model="dateTo" />
        </div>
        <div class="sort-wrap">
          <button class="sbtn" :class="{ on: store.curSort === 'latest' }" @click="setSort('latest')">최신순</button>
          <button class="sbtn" :class="{ on: store.curSort === 'views' }" @click="setSort('views')">조회수</button>
        </div>
      </div>
    </div>

    <div class="paper-list">
      <div class="empty-state" v-if="loading">데이터를 불러오는 중입니다...</div>
      <div class="empty-state" v-else-if="!filteredPapers.length">조건에 맞는 논문이 없습니다.</div>
      
      <div
        v-for="p in pagedPapers"
        :key="p.id"
        class="pcard"
        @click="store.openPaper(p)"
      >
        <div class="pcard-main">
          <div class="pcard-title">{{ p.title }}</div>
          <div class="pcard-abs">{{ p.abs }}</div>
          <div class="pcard-meta">
            <span>{{ p.authors ? p.authors.split(',')[0].trim() + ' et al.' : 'Unknown Authors' }} · {{ p.date }}</span>
            <span>👁 {{ p.views.toLocaleString() }}</span>
          </div>
        </div>
        <div class="pcard-side">
          <span class="pcard-cat-badge" :style="catBadgeStyle(p.cat)">{{ p.cat }}</span>
        </div>
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
import { fetchPapers } from '../api/paperService.js'
import { CL } from '../data/vizData.js'

/** 1. 상수 및 스타일 설정 */
const CATS = ['전체', 'Language & Text', 'Vision & Graphics', 'Robotics & Control', 'Multi-Agent & RL', 'Ethics & Society', 'ML Foundation']

// 디자인 테마를 위한 컬러 맵 생성
const clColorMap = Object.fromEntries(CL.map(c => [c.name, { color: c.color, glow: c.glow }]))

function catBadgeStyle(cat) {
  const c = clColorMap[cat]
  if (!c) return { background: '#334155', color: '#f8fafc', fontSize: '10px', padding: '3px 9px', borderRadius: '20px' }
  return {
    background: c.glow,
    color: c.color,
    border: `1px solid ${c.color}55`,
    fontSize: '10px',
    padding: '3px 9px',
    borderRadius: '20px',
    fontWeight: '600',
    whiteSpace: 'nowrap',
    display: 'inline-block'
  }
}

/** 2. 상태 관리 (State) */
const dateFrom = ref('')
const dateTo = ref('')
const papers = ref([])
const loading = ref(false)

const PAGE_SIZE = 10
const currentPage = ref(1)

/** 3. 데이터 변환 및 로드 로직 */
function transformPaper(p) {
  let authors = ''
  try { 
    // 저자 데이터가 문자열인 경우와 JSON 리스트인 경우 모두 대응
    const authData = p.metadata?.authors
    authors = typeof authData === 'string' && authData.startsWith('[') 
      ? JSON.parse(authData).join(', ') 
      : (authData || '')
  } catch {
    authors = p.metadata?.authors || ''
  }

  return {
    id: p.paper_id,
    title: p.metadata?.title || p.paper_id,
    abs: (p.summary_data?.summary || '').slice(0, 200) + '...',
    summ: p.summary_data?.summary || '',
    authors: authors,
    date: (p.metadata?.published_at || '').slice(0, 10),
    views: Math.floor(Math.random() * 100), // 실데이터 없을 시 랜덤값 (추후 API 반영 가능)
    tags: (p.metadata?.arxiv_categories || '').split(',').map(s => s.trim()).filter(Boolean),
    cat: p.metadata?.category || 'ML Foundation',
    paper_url: p.metadata?.url || '',
    pdf_url: p.metadata?.pdf_url || '',
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const raw = await fetchPapers(100)
    papers.value = raw.map(transformPaper)
  } catch (err) {
    console.error("논문 리스트 로드 실패:", err)
  } finally {
    loading.value = false
  }
})

/** 4. 필터 및 정렬 제어 */
function setCat(c) { store.curCat = c }
function setSort(s) { store.curSort = s }

const filteredPapers = computed(() => {
  let list = [...papers.value]
  
  // 카테고리 필터링
  if (store.curCat !== '전체') {
    list = list.filter(p => p.cat === store.curCat || p.tags.includes(store.curCat))
  }
  
  // 검색어 필터링
  if (store.searchQuery) {
    const lq = store.searchQuery.toLowerCase()
    list = list.filter(p => p.title.toLowerCase().includes(lq))
  }
  
  // 날짜 필터링
  if (dateFrom.value) list = list.filter(p => p.date >= dateFrom.value)
  if (dateTo.value) list = list.filter(p => p.date <= dateTo.value)
  
  // 정렬 (최신순 vs 조회수)
  list.sort(store.curSort === 'views' 
    ? (a, b) => b.views - a.views 
    : (a, b) => b.date.localeCompare(a.date)
  )
  
  return list
})

const totalPages = computed(() => Math.ceil(filteredPapers.value.length / PAGE_SIZE))
const pagedPapers = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredPapers.value.slice(start, start + PAGE_SIZE)
})
const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  const s = Math.max(1, cur - 2)
  const e = Math.min(total, s + 4)
  return Array.from({ length: e - s + 1 }, (_, i) => s + i)
})

watch([() => store.curCat, dateFrom, dateTo, () => store.curSort, () => store.searchQuery], () => {
  currentPage.value = 1
})
</script>

<style scoped>
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