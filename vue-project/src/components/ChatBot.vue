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
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-bubble"
        :class="[msg.role, { typing: msg.typing }]"
      >
        <template v-if="msg.typing">
          <span></span><span></span><span></span>
        </template>
        <template v-else>{{ msg.text }}</template>
      </div>
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
      />
      <button id="chat-send" @click="sendChat">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const isOpen = ref(false)
const initialized = ref(false)
const showChips = ref(true)
const inputText = ref('')
const messages = ref([])
const msgsRef = ref(null)
const inputRef = ref(null)

const chips = ['최신 논문 추천해줘', 'NLP 논문 요약해줘', '논문 비교 방법 알려줘', '사내 비교문서 만드는 법']

const BOT_REPLIES = {
  '최신 논문': '현재 탐색 페이지에서 최신 논문 7편을 확인할 수 있어요. NLP, 언어모델, 그래프 신경망 등 다양한 분야를 다루고 있습니다. 논문 카드를 클릭하면 요약보고서를 볼 수 있어요.',
  'nlp': 'NLP 관련 논문으로는 Attention Is All You Need, BERT 등이 있습니다. 논문리스트 탭에서 NLP 카테고리를 확인해보세요.',
  '요약': '논문 요약은 각 논문 카드를 클릭하면 바로 볼 수 있어요. 더 자세한 요약보고서는 "논문 보러가기" 버튼을 눌러 확인하세요.',
  '비교': '두 논문을 비교하려면 논문리스트에서 논문을 선택 후 관련 사내 문서의 "생성하기" 버튼을 눌러 비교보고서를 만들어보세요.',
  '사내': '사내 비교문서는 논문리스트 → 논문 선택 → 관련 사내 문서 → 생성하기 버튼 순서로 만들 수 있어요. 만들어진 문서는 "비교보고서" 탭에서 모아볼 수 있습니다.',
  '보고서': '비교보고서는 상단 내비게이션의 "비교보고서" 탭에서 지금까지 생성한 목록을 확인할 수 있어요.',
}
const DEFAULTS = [
  '죄송해요, 아직 그 내용은 학습되지 않았어요. 논문 검색, 요약, 비교에 관한 질문을 해주세요!',
  '좋은 질문이에요! 논문 탐색 페이지에서 관련 논문을 찾아보거나, 구체적인 키워드로 다시 질문해 주세요.',
  '현재 시스템에서는 논문 요약 및 비교 기능을 지원해요. 다른 기능은 곧 업데이트 예정입니다.',
]
let defIdx = 0

function getBotReply(txt) {
  const lower = txt.toLowerCase()
  for (const [key, reply] of Object.entries(BOT_REPLIES)) {
    if (lower.includes(key)) return reply
  }
  return DEFAULTS[defIdx++ % DEFAULTS.length]
}

function scrollBottom() {
  nextTick(() => { if (msgsRef.value) msgsRef.value.scrollTop = msgsRef.value.scrollHeight })
}

function addBot(text) {
  // remove typing bubble
  const ti = messages.value.findIndex(m => m.typing)
  if (ti !== -1) messages.value.splice(ti, 1)
  messages.value.push({ role: 'bot', text })
  scrollBottom()
}

function showTyping(cb) {
  messages.value.push({ role: 'bot', typing: true, text: '' })
  scrollBottom()
  setTimeout(cb, 900)
}

function sendChip(txt) {
  messages.value.push({ role: 'user', text: txt })
  showChips.value = false
  showTyping(() => addBot(getBotReply(txt)))
  scrollBottom()
}

function sendChat() {
  const txt = inputText.value.trim()
  if (!txt) return
  inputText.value = ''
  messages.value.push({ role: 'user', text: txt })
  showTyping(() => addBot(getBotReply(txt)))
  scrollBottom()
}

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value && !initialized.value) {
    initialized.value = true
    setTimeout(() => addBot("안녕하세요! 👋 baggin' AI입니다.\n논문 검색, 요약, 비교 분석을 도와드릴게요. 무엇이 궁금하신가요?"), 200)
  }
  if (isOpen.value) setTimeout(() => inputRef.value?.focus(), 250)
}
</script>
