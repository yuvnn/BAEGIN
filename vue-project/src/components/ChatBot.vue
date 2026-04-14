<template>
  <button id="chat-fab" :class="{ open: isOpen }" @click="toggleChat">
    <svg class="chat-icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    <svg class="chat-close" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
  </button>

  <div id="chat-window" :class="{ open: isOpen }">
    <div class="chat-head">
      <div class="chat-head-dot"></div>
      <div>
        <div class="chat-head-name">baggin' AI</div>
        <div class="chat-head-sub">논문 검색 · 요약 · 비교 도우미</div>
      </div>
    </div>

    <div class="chat-msgs" ref="msgsRef">
      <template v-for="(msg, i) in messages" :key="i">
        <!-- 일반 텍스트 버블 -->
        <div
          v-if="msg.type === 'text' || msg.type === 'typing'"
          class="chat-bubble"
          :class="[msg.role, { typing: msg.type === 'typing' }]"
        >
          <template v-if="msg.type === 'typing'">
            <span></span><span></span><span></span>
          </template>
          <template v-else>{{ msg.text }}</template>
        </div>

        <!-- 추천 논문 카드 -->
        <div v-else-if="msg.type === 'papers'" class="chat-cards">
          <div
            v-for="p in msg.papers"
            :key="p.paper_id"
            class="chat-paper-card"
            @click="goToPaper(p.paper_id)"
          >
            <div class="cpc-category">{{ p.category }}</div>
            <div class="cpc-id">{{ p.paper_id }}</div>
            <div class="cpc-reason">{{ p.reason }}</div>
          </div>
        </div>
      </template>
    </div>

    <div class="chat-chips" v-if="showChips">
      <button class="chat-chip" v-for="chip in chips" :key="chip" @click="sendChip(chip)">{{ chip }}</button>
    </div>

    <div class="chat-input-row">
      <input
        id="chat-input"
        ref="inputRef"
        type="text"
        v-model="inputText"
        placeholder="논문에 대해 무엇이든 물어보세요…"
        @keydown.enter="sendChat"
        :disabled="loading"
      />
      <button id="chat-send" @click="sendChat" :disabled="loading">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { store } from '../store.js'

const CHATBOT_URL = 'http://localhost:18086/chatbot/recommend'

const isOpen = ref(false)
const initialized = ref(false)
const showChips = ref(true)
const inputText = ref('')
const loading = ref(false)
const messages = ref([])
const msgsRef = ref(null)
const inputRef = ref(null)

const chips = ['최신 논문 추천해줘', 'NLP 관련 논문 알려줘', '강화학습 논문 있어?', '사용 방법 알려줘']

function scrollBottom() {
  nextTick(() => {
    if (msgsRef.value) msgsRef.value.scrollTop = msgsRef.value.scrollHeight
  })
}

function addMessage(msg) {
  messages.value.push(msg)
  scrollBottom()
}

function removeTyping() {
  const idx = messages.value.findIndex(m => m.type === 'typing')
  if (idx !== -1) messages.value.splice(idx, 1)
}

function showTyping() {
  addMessage({ role: 'bot', type: 'typing' })
}

async function callChatbot(question) {
  try {
    const res = await fetch(CHATBOT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch (e) {
    console.error('Chatbot API error:', e)
    return {
      content: '죄송합니다. 서버에 연결할 수 없습니다. Docker 컨테이너(chatbot-service)가 실행 중인지 확인해주세요.',
      recommended_papers: [],
    }
  }
}

async function handleUserMessage(text) {
  loading.value = true
  showChips.value = false
  showTyping()

  const data = await callChatbot(text)
  removeTyping()

  // 응답 텍스트
  if (data.content) {
    addMessage({ role: 'bot', type: 'text', text: data.content })
  }

  // 추천 논문 카드
  if (data.recommended_papers && data.recommended_papers.length > 0) {
    addMessage({ role: 'bot', type: 'papers', papers: data.recommended_papers })
  }

  loading.value = false
}

function sendChip(txt) {
  addMessage({ role: 'user', type: 'text', text: txt })
  handleUserMessage(txt)
}

function sendChat() {
  const txt = inputText.value.trim()
  if (!txt || loading.value) return
  inputText.value = ''
  addMessage({ role: 'user', type: 'text', text: txt })
  handleUserMessage(txt)
}

function goToPaper(paperId) {
  // paper-service의 paper_id(예: "arxiv:2604.09409")를 store로 전달
  // 현재 store는 로컬 data/papers.js 기준이므로 P2(논문리스트)로 이동 후 검색
  store.doSearch(paperId.replace('arxiv:', ''))
}

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value && !initialized.value) {
    initialized.value = true
    setTimeout(() => {
      addMessage({
        role: 'bot',
        type: 'text',
        text: "안녕하세요! 👋 baggin' AI입니다.\n논문 검색, 요약, 비교 분석을 도와드릴게요. 무엇이 궁금하신가요?",
      })
    }, 200)
  }
  if (isOpen.value) setTimeout(() => inputRef.value?.focus(), 250)
}
</script>

<style scoped>
.chat-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 8px;
  width: 100%;
}

.chat-paper-card {
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.25);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.chat-paper-card:hover {
  background: rgba(37, 99, 235, 0.16);
  border-color: rgba(37, 99, 235, 0.5);
}

.cpc-category {
  font-size: 10px;
  color: #6b9bfa;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 3px;
}

.cpc-id {
  font-size: 11px;
  color: #c8d4ff;
  font-weight: 500;
  margin-bottom: 4px;
  word-break: break-all;
}

.cpc-reason {
  font-size: 11px;
  color: rgba(200, 212, 255, 0.7);
  line-height: 1.4;
}
</style>
