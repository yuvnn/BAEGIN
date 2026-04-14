<template>
  <div class="splash" :class="{ 'splash-out': leaving }">
    <div class="splash-logo">baggin'</div>
  </div>
</template>

<script setup>
defineProps({ leaving: Boolean })
</script>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  opacity: 1;
  transition: opacity 0.5s ease;
}
.splash-out {
  opacity: 0;
  pointer-events: none;
}
.splash-logo {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.04em;
  animation: splash-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes splash-in {
  from { opacity: 0; transform: scale(0.85); }
  to   { opacity: 1; transform: scale(1); }
}
</style>
