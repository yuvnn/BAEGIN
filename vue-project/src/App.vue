<template>
  <template v-if="store.isLoggedIn">
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
</script>
