<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-logo">baggin'</div>
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

<style scoped>
.auth-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d0d0d;
}
.auth-card {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 48px 40px;
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.auth-logo {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}
.auth-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}
.auth-input {
  width: 100%;
  box-sizing: border-box;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 11px 14px;
  color: #fff;
  font-size: 14px;
  outline: none;
}
.auth-input:focus { border-color: #555; }
.auth-btn {
  width: 100%;
  padding: 11px;
  background: #fff;
  color: #000;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}
.auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-link {
  font-size: 12px;
  color: #666;
  cursor: pointer;
  text-align: center;
}
.auth-link span { color: #aaa; text-decoration: underline; }
.auth-link:hover span { color: #fff; }
.auth-error {
  color: #e55;
  font-size: 13px;
  margin: 0;
}
</style>
