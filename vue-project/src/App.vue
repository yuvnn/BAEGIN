<template>
  <main class="container">
    <h1>Paper Monitoring Platform</h1>
    <p class="sub">논문 요약 및 사내 문서 비교 템플릿</p>
    <DashboardView />
  </main>
</template>

<script setup>
import DashboardView from "./views/DashboardView.vue";
</script>

<style scoped>
.container {
  max-width: 100%;
  margin: 0 auto;
  padding: 24px;
  font-family: "Pretendard", "Noto Sans KR", sans-serif;
}

.sub {
  color: #4b5563;
  margin-bottom: 20px;
}
</style>
