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
          <span v-for="t in p.tags.slice(0, 2)" :key="t" class="tag" :class="CAT_TAG[p.cat] || 'tt'">{{ t }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store.js'
import { PAPERS, CATS, CAT_TAG } from '../data/papers.js'

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
