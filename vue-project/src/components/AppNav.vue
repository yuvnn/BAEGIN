<template>
  <nav class="nav">
    <div class="nav-logo" @click="onLogoClick">baggin'</div>
    <div class="nav-links">
      <button class="nav-btn" :class="{ on: store.currentPage === 'p1' }" @click="store.go('p1')">탐색</button>
      <span class="nav-sep">|</span>
      <button class="nav-btn" :class="{ on: store.currentPage === 'p2' || store.currentPage === 'p3' }" @click="store.go('p2')">논문리스트</button>
      <span class="nav-sep">|</span>
      <button class="nav-btn" :class="{ on: store.currentPage === 'p5' || store.currentPage === 'p4' }" @click="store.go('p5')">비교보고서</button>
      <span class="nav-sep">|</span>
      <button class="nav-btn" :class="{ on: store.currentPage === 'p6' }" @click="store.go('p6')">AI 리뷰어</button>
    </div>
    <div class="search-box">
      <input
        type="text"
        v-model="searchInput"
        placeholder="논문 검색..."
        @keydown.enter="doSearch"
      />
      <button class="btn-s" @click="doSearch">검색</button>
      <div class="prof-wrap" ref="profWrapRef">
        <button class="prof-btn" @click="toggleProf" title="프로필">{{ userInitials }}</button>
        <div class="prof-drop" :class="{ open: profOpen }">
          <div class="prof-info">
            <div class="prof-avatar">{{ userInitials }}</div>
            <div>
              <div class="prof-name">{{ userName }}</div>
              <div class="prof-email">{{ userEmail }}</div>
            </div>
          </div>
          <div class="prof-item"><span class="prof-item-icon">⚙</span>설정</div>
          <div class="prof-item"><span class="prof-item-icon">🔔</span>알림</div>
          <div class="prof-item"><span class="prof-item-icon">👤</span>마이페이지</div>
          <div class="prof-div"></div>
          <div class="prof-item prof-logout" @click="doLogout"><span class="prof-item-icon">→</span>로그아웃</div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { store } from '../store.js'

const searchInput = ref('')
const profOpen = ref(false)
const profWrapRef = ref(null)

const userName = computed(() => store.user?.name || store.user?.email || '사용자')
const userEmail = computed(() => store.user?.email || '')
const userInitials = computed(() => {
  const n = store.user?.name || store.user?.email || '?'
  return n.slice(0, 2).toUpperCase()
})

function onLogoClick() {
  window.location.reload()
}

function doSearch() {
  const q = searchInput.value.trim()
  store.doSearch(q)
}

function toggleProf() {
  profOpen.value = !profOpen.value
}

function doLogout() {
  profOpen.value = false
  store.logout()
}

function onDocClick(e) {
  if (profWrapRef.value && !profWrapRef.value.contains(e.target)) {
    profOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))
</script>
