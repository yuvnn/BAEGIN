<template>
  <main class="container">
    <DashboardView />
  </main>
</template>

<script setup>
import DashboardView from "./views/DashboardView.vue";
</script>

<style scoped>
:global(html),
:global(body),
:global(#app) {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.container {
  width: 100vw;
  height: 100vh;
  max-width: none;
  margin: 0;
  padding: 0;
  font-family: "Pretendard", "Noto Sans KR", sans-serif;
}

.sub {
  color: #4b5563;
  margin-bottom: 20px;
}
</style>
