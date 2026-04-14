<template>
  <div id="p5" class="page">
    <div class="p2-head">
      <div class="pg-title">사내 비교문서 목록</div>
    </div>
    <div class="paper-list">
      <div class="empty-state" v-if="!store.generatedReports.length">
        생성하기 버튼을 눌러 첫 사내 비교문서를 만들어보세요.
      </div>
      <div
        v-for="(r, i) in store.generatedReports"
        :key="i"
        class="rcard"
        @click="store.viewReport(i)"
      >
        <div class="pcard-main">
          <div class="pcard-title">{{ r.docName }}</div>
          <div class="pcard-abs" style="margin-bottom:4px;">관련 논문: {{ r.paperTitle }}</div>
          <div class="pcard-meta"><span class="rcard-date">{{ r.createdAt }} 생성</span></div>
        </div>
        <div class="rcard-badge">열기 →</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { store } from '../store.js'
</script>
