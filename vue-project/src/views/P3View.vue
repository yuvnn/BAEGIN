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
          <span v-for="(t, i) in p.tags" :key="t" class="tag" :class="TAG_C[i % 5]">{{ t }}</span>
        </div>
      </div>
      <div class="dbody">
        <div class="d-orig">
          <div class="sec-head">
            <span>원본</span>
            <button class="btn-back" style="font-size:11px;" @click="store.go('p4')">비교 문서 생성 →</button>
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
            <template v-if="p.relDocs && p.relDocs.length">
              <div v-for="d in p.relDocs" :key="d" class="rel-item-wrap">
                <div class="rel-item-left">
                  <div class="rel-dot"></div>
                  <span>{{ d }}</span>
                </div>
                <button class="btn-gen" @click="store.generateReport(d, p.id)">생성하기</button>
              </div>
            </template>
            <div v-else style="padding:11px 14px;font-size:12px;color:var(--t3)">관련 문서 없음</div>
          </div>
        </div>
      </div>
      <div class="banner" v-if="!p.relDocs || !p.relDocs.length">
        <div class="banner-txt"><strong>관련 사내 문서가 없습니다.</strong> 이 논문을 바탕으로 사내 문서를 만들겠습니까?</div>
        <button class="btn-mk" @click="store.go('p4')">만들겠습니다</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store } from '../store.js'
import { TAG_C } from '../data/papers.js'
import { fmt, fmtMd } from '../utils/format.js'

const p = computed(() => store.curPaper)
const bcTitle = computed(() => { const t = p.value.title; return t.length > 45 ? t.slice(0, 45) + '…' : t })
const origHtml = computed(() => fmt(p.value.orig || ''))
const summHtml = computed(() => fmtMd(p.value.summ || ''))
</script>
