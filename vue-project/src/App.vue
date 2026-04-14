<template>
  <SplashView v-if="splashVisible" :leaving="splashLeaving" />
  <template v-else-if="store.isLoggedIn">
    <AppNav />
    <P1View v-show="store.currentPage === 'p1'" />
    <P2View v-show="store.currentPage === 'p2'" />
    <P3View v-show="store.currentPage === 'p3'" />
    <P4View v-show="store.currentPage === 'p4'" />
    <P5View v-show="store.currentPage === 'p5'" />
    <P6View v-show="store.currentPage === 'p6'" />
    <ChatBot />
  </template>
  <template v-else>
    <LoginView v-if="store.currentPage !== 'signup'" />
    <SignupView v-else />
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { store } from './store.js'
import AppNav from './components/AppNav.vue'
import ChatBot from './components/ChatBot.vue'
import P1View from './views/P1View.vue'
import P2View from './views/P2View.vue'
import P3View from './views/P3View.vue'
import P4View from './views/P4View.vue'
import P5View from './views/P5View.vue'
import P6View from './views/P6View.vue'
import LoginView from './views/LoginView.vue'
import SignupView from './views/SignupView.vue'
import SplashView from './views/SplashView.vue'

const splashVisible = ref(true)
const splashLeaving = ref(false)

onMounted(() => {
  setTimeout(() => {
    splashLeaving.value = true
    setTimeout(() => {
      splashVisible.value = false
    }, 500)
  }, 1500)
})
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
