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
      <div class="empty-state" v-if="!filteredPapers.length">검색 결과가 없습니다.</div>
      <div
        v-for="p in filteredPapers"
        :key="p.id"
        class="pcard"
        @click="store.openPaper(p.id)"
      >
        <div class="pcard-main">
          <div class="pcard-title">{{ p.title }}</div>
          <div class="pcard-abs">{{ p.abs }}</div>
          <div class="pcard-meta">
            <span>{{ p.authors.split(',')[0].trim() }} et al. · {{ p.date }}</span>
            <span>👁 {{ p.views.toLocaleString() }}</span>
          </div>
        </div>
        <div class="pcard-side">
          <span class="pcard-cat-badge" :style="catBadgeStyle(p.cat)">{{ p.cat }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store.js'
import { PAPERS, CATS } from '../data/papers.js'
import { CL } from '../data/vizData.js'

const clColorMap = Object.fromEntries(CL.map(c => [c.name, { color: c.color, glow: c.glow }]))

function catBadgeStyle(cat) {
  const c = clColorMap[cat]
  if (!c) return {}
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

const dateFrom = ref('')
const dateTo = ref('')

function setCat(c) { store.curCat = c }
function setSort(s) { store.curSort = s }

const filteredPapers = computed(() => {
  let list = [...PAPERS]
  if (store.curCat !== '전체') list = list.filter(p => p.cat === store.curCat || p.tags.includes(store.curCat))
  if (store.searchQuery) {
    const lq = store.searchQuery.toLowerCase()
    list = list.filter(p => p.title.toLowerCase().includes(lq))
  }
  if (dateFrom.value) list = list.filter(p => p.date >= dateFrom.value)
  if (dateTo.value) list = list.filter(p => p.date <= dateTo.value)
  list.sort(store.curSort === 'views' ? (a, b) => b.views - a.views : (a, b) => b.date.localeCompare(a.date))
  return list
})
</script>
