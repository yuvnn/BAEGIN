<template>
  <section class="panel">
    <h2>Monitoring Trigger</h2>
    <div class="row">
      <input v-model="keyword" placeholder="예: battery recycling" />
      <button @click="onRun" :disabled="loading">실행</button>
    </div>

    <p v-if="loading">처리 중...</p>
    <pre v-else-if="result">{{ result }}</pre>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { runMonitoring } from "../api/paperService";

const keyword = ref("battery AI");
const loading = ref(false);
const result = ref(null);

async function onRun() {
  loading.value = true;
  try {
    result.value = await runMonitoring(keyword.value);
  } catch (error) {
    result.value = { error: error.message };
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.panel {
  border: 1px solid #d1d5db;
  border-radius: 12px;
  padding: 20px;
}

.row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

input {
  flex: 1;
  padding: 8px;
}

button {
  padding: 8px 14px;
  border: 0;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
}
</style>
