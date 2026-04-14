<template>
  <div class="auth-wrap">
    <!-- Left: Hero -->
    <div class="auth-hero">
      <div class="hero-inner">
        <div class="hero-logo">baggin'</div>
        <h1 class="hero-headline">세상의 모든 논문을<br>당신의 비즈니스 언어로.</h1>
        <p class="hero-sub">최신 연구를 실무 인사이트로 변환하는<br>AI 논문 분석 플랫폼</p>
        <div class="hero-tags">
          <span>Language & Text</span>
          <span>Vision & Graphics</span>
          <span>ML Foundation</span>
          <span>Robotics & Control</span>
          <span>Multi-Agent & RL</span>
          <span>Ethics & Society</span>
        </div>
      </div>
    </div>

    <!-- Right: Login Form -->
    <div class="auth-right">
      <div class="auth-card">
        <h2 class="auth-title">로그인</h2>

        <input
          class="auth-input"
          type="email"
          v-model="email"
          placeholder="이메일"
          @keydown.enter="focusPassword"
          ref="emailInput"
        />
        <input
          class="auth-input"
          type="password"
          v-model="password"
          placeholder="비밀번호"
          @keydown.enter="doLogin"
          ref="passwordInput"
        />

        <p v-if="error" class="auth-error">{{ error }}</p>

        <button class="auth-btn" @click="doLogin" :disabled="logging">
          {{ logging ? '로그인 중...' : '로그인하기' }}
        </button>

        <p class="auth-link" @click="goSignup">계정이 없으신가요? <span>회원가입</span></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store } from '../store.js'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const email = ref('')
const password = ref('')
const error = ref('')
const logging = ref(false)
const emailInput = ref(null)
const passwordInput = ref(null)

function goSignup() {
  store.currentPage = 'signup'
}

function focusPassword() {
  passwordInput.value?.focus()
}

async function doLogin() {
  error.value = ''
  if (!email.value.trim()) { error.value = '이메일을 입력하세요.'; return }
  if (!password.value) { error.value = '비밀번호를 입력하세요.'; return }
  logging.value = true
  try {
    const res = await axios.post(`${BASE_URL}/api/auth/login`, {
      email: email.value.trim(),
      password: password.value,
    })
    store.login(res.data.access_token, res.data.user)
  } catch (e) {
    error.value = e.response?.data?.error || '로그인에 실패했습니다.'
  } finally {
    logging.value = false
  }
}
</script>

<style>
.auth-wrap {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: row;
  width: 100%;
}

/* ── Left Hero ── */
.auth-hero {
  flex: 1;
  width: 50%;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 56px;
  border-right: 1px solid #1e1e1e;
  position: relative;
  overflow: hidden;
}
.auth-hero::before {
  content: '';
  position: absolute;
  top: -120px;
  left: -80px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(79,142,245,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.auth-hero::after {
  content: '';
  position: absolute;
  bottom: -80px;
  right: -60px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(192,132,252,0.09) 0%, transparent 70%);
  pointer-events: none;
}
.hero-inner {
  position: relative;
  z-index: 1;
  max-width: 420px;
}
.hero-logo {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(120,160,255,0.7);
  margin-bottom: 32px;
}
.hero-headline {
  font-size: 38px;
  font-weight: 700;
  line-height: 1.25;
  color: #fff;
  margin: 0 0 20px;
  letter-spacing: -0.02em;
}
.hero-sub {
  font-size: 15px;
  color: rgba(160,180,220,0.6);
  line-height: 1.7;
  margin: 0 0 36px;
}
.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.hero-tags span {
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(200,220,255,0.5);
  background: rgba(255,255,255,0.03);
}

/* ── Right Login ── */
.auth-right {
  flex: 1;
  width: 50%;
  background: #0d0d0d;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 56px;
}
.auth-card {
  width: 100%;
  max-width: 340px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.auth-title {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px;
}
.auth-input {
  width: 100%;
  box-sizing: border-box;
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 12px 14px;
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color .2s;
}
.auth-input:focus { border-color: #444; }
.auth-btn {
  width: 100%;
  padding: 12px;
  background: #fff;
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
  transition: opacity .2s;
}
.auth-btn:hover { opacity: 0.88; }
.auth-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.auth-link {
  font-size: 12px;
  color: #555;
  cursor: pointer;
  text-align: center;
}
.auth-link span { color: #888; text-decoration: underline; }
.auth-link:hover span { color: #fff; }
.auth-error {
  color: #e55;
  font-size: 13px;
  margin: 0;
}
</style>
