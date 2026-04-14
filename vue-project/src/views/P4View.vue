<template>
  <div id="p4" class="page" style="height:calc(100vh - 52px);">
    <div class="c4-head">
      <div class="c4-title">사내 비교 문서</div>
      <button class="btn-back" @click="store.go('p3')">← 논문으로 돌아가기</button>
    </div>
    <div class="c4-body">
      <div class="c4-left">
        <div class="c4-phead">비교 문서 / 인사이트 보고서</div>
        <div class="c4-content" v-html="reportHtml"></div>
      </div>
      <div class="c4-right">
        <div class="c4-tabs">
          <button class="ctab" :class="{ on: activeTab === 't1' }" @click="activeTab = 't1'">사내문서</button>
          <button class="ctab" :class="{ on: activeTab === 't2' }" @click="activeTab = 't2'">논문 요약서</button>
          <button class="ctab" :class="{ on: activeTab === 't3' }" @click="activeTab = 't3'">논문원문</button>
        </div>
        <div v-show="activeTab === 't1'" class="c4-content" v-html="t1Html"></div>
        <div v-show="activeTab === 't2'" class="c4-content" v-html="t2Html"></div>
        <div v-show="activeTab === 't3'" class="c4-content" v-html="t3Html"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store.js'
import { fmt, fmtMd } from '../utils/format.js'

const activeTab = ref('t1')

const p = computed(() => store.p4Paper)

const shortTitle = computed(() => { const t = p.value.title; return t.length > 38 ? t.slice(0, 38) + '…' : t })

const reportHtml = computed(() => `
  <div class="ins-sec"><h3>📋 인사이트 보고서: ${shortTitle.value}</h3></div>
  <div class="ins-sec"><h3>1. 논문 핵심 요약</h3>${fmtMd(p.value.summ || '')}</div>
  <div class="ins-sec"><h3>2. 사내 적용 가능성</h3>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>예상 성능 개선: <strong style="color:var(--teal)">중-상</strong></span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>구현 복잡도: <strong style="color:var(--orange)">중간</strong></span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>필요 자원: GPU 클러스터 최소 4대 이상</span></div>
  </div>
  <div class="ins-sec"><h3>3. 경쟁사 동향</h3>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>A사: 유사 기술 적용 완료 (2023 Q4)</span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>B사: 파일럿 프로그램 진행 중</span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>C사: 미도입 — 당사 선점 기회 존재</span></div>
  </div>
  <div class="ins-sec"><h3>4. 권고 사항</h3>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>단기(1-3개월): PoC 진행 및 벤치마크 수행</span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>중기(3-6개월): 파일럿 서비스 론칭</span></div>
    <div class="ins-pt"><span class="ins-bul">▶</span><span>장기(6-12개월): 전사 적용 검토</span></div>
  </div>
`)

const t1Html = computed(() => `
  <div class="ins-sec"><h3>사내 기술 검토 문서</h3><p>작성일: ${p.value.date} | 작성자: AI Research Team</p></div>
  <div class="ins-sec"><h3>개요</h3><p>${p.value.abs || ''}</p></div>
  <div class="ins-sec"><h3>기술 검토 결과</h3>
    <div class="ins-pt"><span class="ins-bul">✓</span><span>알고리즘 검증: 완료</span></div>
    <div class="ins-pt"><span class="ins-bul">✓</span><span>사내 환경 호환성: 확인 필요</span></div>
    <div class="ins-pt"><span class="ins-bul">✓</span><span>라이선스: 오픈소스 (Apache 2.0)</span></div>
  </div>
  <div class="ins-sec"><h3>관련 사내 프로젝트</h3>${(p.value.relDocs || []).map(d => `<div class="ins-pt"><span class="ins-bul">→</span><span>${d}</span></div>`).join('')}</div>
`)

const t2Html = computed(() => `
  <div style="font-size:15px;font-weight:600;color:var(--t1);margin-bottom:12px;">${p.value.title}</div>
  <div style="font-size:12px;color:var(--t3);margin-bottom:16px;">${p.value.authors} · ${p.value.date}</div>
  ${fmtMd(p.value.summ || '')}
`)

const t3Html = computed(() => `
  <div style="font-size:15px;font-weight:600;color:var(--t1);margin-bottom:12px;">${p.value.title}</div>
  <div style="font-size:12px;color:var(--t3);margin-bottom:16px;">${p.value.authors} · ${p.value.date}</div>
  ${fmt(p.value.orig || '')}
`)
</script>
