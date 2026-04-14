<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="auth-logo">baggin'</div>
      <h2 class="auth-title">회원가입</h2>

      <!-- Step indicator -->
      <div class="steps">
        <div class="step" :class="{ active: step >= 1, done: step > 1 }">
          <span class="step-num">1</span>
          <span class="step-label">기본 정보</span>
        </div>
        <div class="step-line" :class="{ done: step > 1 }"></div>
        <div class="step" :class="{ active: step >= 2, done: step > 2 }">
          <span class="step-num">2</span>
          <span class="step-label">관심 분야</span>
        </div>
        <div class="step-line" :class="{ done: step > 2 }"></div>
        <div class="step" :class="{ active: step >= 3 }">
          <span class="step-num">3</span>
          <span class="step-label">본인인증</span>
        </div>
      </div>

      <!-- Step 1: Basic Info -->
      <div v-if="step === 1" class="step-body">
        <input class="auth-input" type="text" v-model="name" placeholder="이름" @keydown.enter="focusEmail" ref="nameInput" />
        <input class="auth-input" type="email" v-model="email" placeholder="이메일" @keydown.enter="focusPw" ref="emailInput" />
        <input class="auth-input" type="password" v-model="password" placeholder="비밀번호" @keydown.enter="focusPwConfirm" ref="pwInput" />
        <input class="auth-input" type="password" v-model="passwordConfirm" placeholder="비밀번호 확인" @keydown.enter="goStep2" ref="pwConfirmInput" />
        <p v-if="error" class="auth-error">{{ error }}</p>
        <button class="auth-btn" @click="goStep2">다음</button>
        <p class="auth-link" @click="store.currentPage = 'login'">이미 계정이 있으신가요? <span>로그인</span></p>
      </div>

      <!-- Step 2: Category keywords -->
      <div v-if="step === 2" class="step-body">
        <p class="auth-desc">관심 분야를 선택하세요. (복수 선택 가능)</p>
        <div class="cat-grid">
          <button
            v-for="cat in CATEGORIES"
            :key="cat.value"
            class="cat-btn"
            :class="{ selected: selectedCats.includes(cat.value) }"
            @click="toggleCat(cat.value)"
          >
            {{ cat.label }}
          </button>
        </div>
        <p v-if="error" class="auth-error">{{ error }}</p>
        <button class="auth-btn" @click="goStep3">다음</button>
        <p class="auth-link" @click="step = 1">← 뒤로</p>
      </div>

      <!-- Step 3: Slack OTP -->
      <div v-if="step === 3" class="step-body">
        <p class="auth-desc">Slack으로 인증 코드를 전송합니다.<br /><span class="auth-email-hint">{{ email }}</span></p>
        <button v-if="!otpSent" class="auth-btn-outline" @click="sendOtp" :disabled="sending">
          {{ sending ? '전송 중...' : 'Slack으로 코드 전송' }}
        </button>
        <div v-if="otpSent">
          <p class="auth-desc sent-hint">코드가 전송되었습니다. Slack을 확인하세요.</p>
          <input
            class="auth-input"
            type="text"
            v-model="otp"
            placeholder="6자리 코드"
            maxlength="6"
            @keydown.enter="doRegister"
          />
        </div>
        <p v-if="error" class="auth-error">{{ error }}</p>
        <button v-if="otpSent" class="auth-btn" @click="doRegister" :disabled="registering">
          {{ registering ? '처리 중...' : '가입 완료' }}
        </button>
        <p class="auth-link" @click="step = 2">← 뒤로</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store } from '../store.js'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const CATEGORIES = [
  { label: 'Language & Text', value: 'cs.CL' },
  { label: 'Vision & Graphics', value: 'cs.CV' },
  { label: 'Robotics & Control', value: 'cs.RO' },
  { label: 'ML Foundation', value: 'cs.LG' },
  { label: 'Multi-Agent & RL', value: 'cs.MA' },
  { label: 'Ethics & Society', value: 'cs.CY' },
]

const step = ref(1)
const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const otp = ref('')
const otpSent = ref(false)
const selectedCats = ref([])
const error = ref('')
const sending = ref(false)
const registering = ref(false)

const nameInput = ref(null)
const emailInput = ref(null)
const pwInput = ref(null)
const pwConfirmInput = ref(null)

function focusEmail() { emailInput.value?.focus() }
function focusPw() { pwInput.value?.focus() }
function focusPwConfirm() { pwConfirmInput.value?.focus() }

function toggleCat(val) {
  const idx = selectedCats.value.indexOf(val)
  if (idx >= 0) selectedCats.value.splice(idx, 1)
  else selectedCats.value.push(val)
}

function goStep2() {
  error.value = ''
  if (!name.value.trim()) { error.value = '이름을 입력하세요.'; return }
  if (!email.value.trim()) { error.value = '이메일을 입력하세요.'; return }
  if (!password.value) { error.value = '비밀번호를 입력하세요.'; return }
  if (password.value.length < 6) { error.value = '비밀번호는 6자 이상이어야 합니다.'; return }
  if (password.value !== passwordConfirm.value) { error.value = '비밀번호가 일치하지 않습니다.'; return }
  step.value = 2
}

function goStep3() {
  error.value = ''
  if (selectedCats.value.length === 0) { error.value = '관심 분야를 하나 이상 선택하세요.'; return }
  step.value = 3
}

async function sendOtp() {
  error.value = ''
  sending.value = true
  try {
    await axios.post(`${BASE_URL}/api/auth/otp/send`, { email: email.value.trim() })
    otpSent.value = true
  } catch (e) {
    error.value = e.response?.data?.error || '전송에 실패했습니다.'
  } finally {
    sending.value = false
  }
}

async function doRegister() {
  error.value = ''
  if (!otp.value.trim()) { error.value = '인증 코드를 입력하세요.'; return }
  registering.value = true
  try {
    const res = await axios.post(`${BASE_URL}/api/auth/register`, {
      email: email.value.trim(),
      name: name.value.trim(),
      password: password.value,
      keywords: selectedCats.value,
      otp: otp.value.trim(),
    })
    store.login(res.data.access_token, res.data.user)
  } catch (e) {
    error.value = e.response?.data?.error || '가입에 실패했습니다.'
  } finally {
    registering.value = false
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
  width: 420px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.auth-logo { font-size: 24px; font-weight: 700; color: #fff; }
.auth-title { font-size: 20px; font-weight: 600; color: #fff; margin: 0; }

/* Step indicator */
.steps {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 4px;
}
.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #2a2a2a;
  border: 1px solid #444;
  color: #666;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.step.active .step-num {
  background: #fff;
  border-color: #fff;
  color: #000;
}
.step.done .step-num {
  background: #444;
  border-color: #444;
  color: #ccc;
}
.step-label {
  font-size: 10px;
  color: #555;
  white-space: nowrap;
}
.step.active .step-label { color: #ccc; }
.step-line {
  flex: 1;
  height: 1px;
  background: #333;
  margin: 0 6px;
  margin-bottom: 14px;
  transition: background 0.2s;
}
.step-line.done { background: #555; }

/* Step body */
.step-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.auth-desc { font-size: 13px; color: #888; margin: 0; line-height: 1.5; }
.auth-email-hint { color: #aaa; }
.sent-hint { color: #6a6; }
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
.cat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.cat-btn {
  padding: 10px 8px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #aaa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.cat-btn:hover { border-color: #555; color: #fff; }
.cat-btn.selected { border-color: #fff; color: #fff; background: #222; }
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
}
.auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-btn-outline {
  width: 100%;
  padding: 11px;
  background: transparent;
  color: #fff;
  border: 1px solid #555;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.15s;
}
.auth-btn-outline:hover { border-color: #aaa; }
.auth-btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-link { font-size: 12px; color: #666; cursor: pointer; text-align: center; }
.auth-link span { color: #aaa; text-decoration: underline; }
.auth-link:hover span { color: #fff; }
.auth-error { color: #e55; font-size: 13px; margin: 0; }
</style>
