<template>
  <div id="p1" class="page">
    <canvas ref="bgCanvasRef" id="bgCanvas"></canvas>
    <div class="p1-body">
      <div class="p1-left" ref="leftPanelRef">
        <canvas ref="vizCanvasRef" id="vizCanvas" :class="{ drag: isDragging }"></canvas>
        <div class="viz-info">드래그로 회전 · 스크롤로 확대/축소</div>
        <!-- Automated Reviewer Panel -->
        <div class="reviewer-panel" @click="store.go('p6')">
          <div class="rp-title-row">
            <div class="rp-title">Automated Reviewer</div>
            <div class="rp-status"><span class="rp-dot"></span>작동중</div>
          </div>
          <div class="rp-desc">3인 심사 앙상블<br>+ 반성 루프 + Area Chair</div>
          <div class="rp-score-row">
            <span class="rp-badge accept">≥ 5.0 Accept</span>
            <span class="rp-badge range">AIRA 1~10</span>
          </div>
          <div class="rp-hint">클릭하여 자세히 보기 →</div>
        </div>
        <div class="p1-legend">
          <div v-for="cl in CL" :key="cl.name" class="p1-legend-item">
            <div class="p1-legend-dot" :style="{ background: cl.color }"></div>
            {{ cl.name }}
          </div>
        </div>
        <!-- Tooltip -->
        <div
          class="beg-tt"
          :style="{ display: tooltip.show ? 'block' : 'none', left: tooltip.left + 'px', top: tooltip.top + 'px' }"
        >
          <div class="tt-title">{{ tooltip.title }}</div>
          <div class="tt-meta">{{ tooltip.meta }}</div>
        </div>
        <!-- Modal -->
        <div class="modal-bg" :class="{ show: store.p1ModalOpen }" @click.self="closeModal">
          <div class="modal">
            <button class="modal-x" @click="closeModal">×</button>
            <div
              class="modal-tag"
              :style="{ background: modal.tagBg, border: modal.tagBorder, color: modal.tagColor }"
            >{{ modal.tagText }}</div>
            <div class="modal-title">{{ modal.title }}</div>
            <div class="modal-authors">{{ modal.auth }}</div>
            <div class="modal-abstract">{{ modal.abs }}</div>
            <div class="modal-row">
              <div class="modal-stat">
                <div class="modal-stat-label">AIRA Score</div>
                <div class="modal-stat-value" :style="{ color: modal.scoreColor }">{{ modal.airaLabel }}</div>
                <div class="mbar"><div class="mbar-fill" :style="modal.mbarStyle"></div></div>
              </div>
              <div class="modal-stat">
                <div class="modal-stat-label">판정</div>
                <div class="modal-stat-value" :style="{ color: decisionColor(modal.decision), fontSize: '11px' }">{{ modal.decision }}</div>
              </div>
              <div class="modal-stat">
                <div class="modal-stat-label">카테고리</div>
                <div class="modal-stat-value" style="color:#c8d4ff;font-size:11px">{{ modal.category }}</div>
              </div>
            </div>
            <div class="modal-summ-section">
              <div class="modal-summ-label">요약보고서</div>
              <div class="modal-summ-body" v-html="modal.summ"></div>
            </div>
            <div class="modal-actions">
              <button class="mbtn" :disabled="!modal.onOpenPaper" @click="modal.onOpenPaper && modal.onOpenPaper()">논문 보러가기 →</button>
            </div>
          </div>
        </div>
      </div>

      <div class="p1-right" style="position:relative;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div class="p1-sec-title">최신 논문</div>
          <div style="display:flex;align-items:center;gap:7px;position:relative;z-index:2;">
            <button class="research-btn" @click="openResearch">논문 조사</button>
            <button class="scan-btn" :class="{ loading: scanning }" :disabled="scanning" @click="triggerScan">
              {{ scanning ? '탐색 중...' : '즉시 탐색' }}
            </button>
            <div class="p1-badge">실시간</div>
          </div>
        </div>
        <div v-if="scanning" class="scan-live-banner">
          <span class="scan-live-dot"></span>
          논문을 탐색하는 중입니다
          <span class="scan-dots"><span>.</span><span>.</span><span>.</span></span>
        </div>
        <div v-if="scanResult" class="scan-toast" :class="{ error: scanResult.error }">
          <template v-if="scanResult.error">탐색 실패. 서비스 상태를 확인하세요.</template>
          <template v-else-if="scanResult.newCount">신규 {{ scanResult.newCount }}편 확인됨 ✓</template>
          <template v-else>탐색 완료. 새 논문이 없습니다.</template>
        </div>

        <!-- 논문 조사 오버레이 패널 -->
        <div v-if="researchOpen" class="research-panel">
          <div class="research-header">
            <span class="research-title">논문 조사</span>
            <button class="research-close" @click="closeResearch">✕</button>
          </div>

          <!-- 날짜 범위 -->
          <div class="research-row">
            <label>날짜</label>
            <input type="date" v-model="researchDateFrom" class="rdate-in" />
            <span style="color:rgba(180,200,255,.4)">~</span>
            <input type="date" v-model="researchDateTo" class="rdate-in" />
          </div>

          <!-- 카테고리 칩 -->
          <div class="research-row" style="align-items:flex-start;flex-direction:column;gap:5px;">
            <label>카테고리</label>
            <div class="rcat-chips">
              <button v-for="cat in RESEARCH_CATS" :key="cat.code"
                class="rcat-chip" :class="{ on: researchCats.includes(cat.code) }"
                @click="toggleCat(cat.code)">{{ cat.label }}</button>
            </div>
          </div>

          <!-- 키워드 -->
          <div class="research-row">
            <label>키워드</label>
            <input type="text" v-model="researchKeywords" class="rkw-in"
              placeholder="transformer, RAG (쉼표 구분)" />
          </div>

          <button class="research-go-btn" :disabled="researching" @click="runResearch">
            {{ researching ? '조사 중...' : '조사 시작' }}
          </button>

          <!-- 로딩 애니메이션 -->
          <div v-if="researching" class="research-loading">
            <div class="research-spinner"></div>
            <span>arXiv에서 논문을 검색하는 중</span>
            <span class="scan-dots"><span>.</span><span>.</span><span>.</span></span>
          </div>

          <!-- 결과 -->
          <template v-if="researchResults">
            <div v-if="researchResults.error" style="font-size:11px;color:#f87171;padding:6px 0;">
              검색 실패. 서비스 상태를 확인하세요.
            </div>
            <template v-else>
              <div class="research-result-count">{{ researchResults.count }}편 발견</div>
              <div class="research-results">
                <div v-for="p in researchResults.papers" :key="p.paper_id" class="research-paper-item">
                  <div class="rp-title">{{ p.title }}</div>
                  <div class="rp-meta">
                    <span>{{ (p.arxiv_categories || []).slice(0,2).join(' · ') }}</span>
                    <span>{{ (p.published_at || '').slice(0,10) }}</span>
                  </div>
                  <div class="rp-abs">{{ (p.abstract || '').slice(0, 120) }}...</div>
                </div>
              </div>
              <div v-if="researchResults.pipeline_queued > 0" class="research-pipeline-badge">
                {{ researchResults.pipeline_queued }}편 분석 파이프라인 전달됨 · 논문 목록에 순차 반영
              </div>
            </template>
          </template>
        </div>

        <div class="plist">
          <div v-if="realPapersLoading" class="plist-empty">불러오는 중...</div>
          <div v-else-if="realPapers.length === 0" class="plist-empty">저장된 논문이 없습니다.</div>
          <div
            v-for="(p, i) in realPapers"
            :key="p.paper_id"
            class="paper"
            :class="{ active: activeRealIdx === i }"
            @click="openRealModal(p, i)"
          >
            <div class="ptop">
              <div class="ptitle">{{ p.metadata?.title || p.paper_id }}</div>
              <div class="pscore" :class="airaScc(p.aira_score)">AIRA {{ p.aira_score != null ? p.aira_score.toFixed(1) : '-' }}</div>
            </div>
            <div class="pmeta">
              <span class="ptag">{{ p.metadata?.category || '-' }}</span>
              <span class="pyear">{{ (p.metadata?.arxiv_categories || '').split(',')[0] }}</span>
            </div>
            <div class="tbar">
              <div class="tbar-fill" :style="airaTbarStyle(p.aira_score)"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { monitoringClient } from '../api/client.js'
import { store } from '../store.js'
import { PP, CL } from '../data/vizData.js'
import { PAPERS } from '../data/papers.js'
import { fmtMd } from '../utils/format.js'
import { fetchPapers, fetchPaperById, searchPapers } from '../api/paperService.js'

const bgCanvasRef = ref(null)
const vizCanvasRef = ref(null)
const leftPanelRef = ref(null)
const isDragging = ref(false)

// 논문 조사 패널
const RESEARCH_CATS = [
  { code: 'cs.CL', label: 'NLP' }, { code: 'cs.CV', label: 'Vision' },
  { code: 'cs.LG', label: 'ML' },  { code: 'cs.AI', label: 'AI' },
  { code: 'cs.RO', label: 'Robotics' }, { code: 'cs.MA', label: 'Multi-Agent' },
  { code: 'stat.ML', label: 'Stat.ML' },
]
const researchOpen = ref(false)
const researching = ref(false)
const researchDateFrom = ref('')
const researchDateTo = ref('')
const researchCats = ref([])
const researchKeywords = ref('')
const researchResults = ref(null)

function openResearch() { researchOpen.value = true; researchResults.value = null }
function closeResearch() { researchOpen.value = false }
function toggleCat(code) {
  const i = researchCats.value.indexOf(code)
  if (i >= 0) researchCats.value.splice(i, 1)
  else researchCats.value.push(code)
}
async function runResearch() {
  if (researching.value) return
  researching.value = true
  researchResults.value = null
  try {
    const kws = researchKeywords.value.split(',').map(k => k.trim()).filter(Boolean)
    const data = await searchPapers({
      dateFrom: researchDateFrom.value || null,
      dateTo: researchDateTo.value || null,
      keywords: kws,
      categories: researchCats.value,
    })
    researchResults.value = data

    // 파이프라인 전달됨 → 논문 목록 폴링 시작
    if (data.pipeline_queued > 0) {
      startResearchPoll(realPapers.value.length)
    }
  } catch {
    researchResults.value = { count: 0, papers: [], error: true }
  } finally {
    researching.value = false
  }
}

let researchPollTimer = null
function startResearchPoll(baseCount) {
  if (researchPollTimer) clearInterval(researchPollTimer)
  let attempts = 0
  researchPollTimer = setInterval(async () => {
    attempts++
    const papers = await fetchPapers(15).catch(() => null)
    if (papers) {
      realPapers.value = papers
      if (papers.length > baseCount) {
        clearInterval(researchPollTimer)
        researchPollTimer = null
        return
      }
    }
    if (attempts >= 10) {
      clearInterval(researchPollTimer)
      researchPollTimer = null
    }
  }, 8000)
}

const realPapers = ref([])
const realPapersLoading = ref(false)
const activeRealIdx = ref(null)
const scanning = ref(false)
const scanResult = ref(null)
let pollTimer = null
let scanPollTimer = null
let scanStopTimer = null
let scanStartCount = 0

async function triggerScan() {
  if (scanning.value) return
  scanning.value = true
  scanResult.value = null
  scanStartCount = realPapers.value.length

  try {
    await monitoringClient.post('/api/monitor/run', { max_results: 50 }, { timeout: 10000 })
  } catch { /* already_running or net error — still poll */ }

  let pollCount = 0
  scanPollTimer = setInterval(async () => {
    pollCount++
    const papers = await fetchPapers(15).catch(() => null)
    if (papers) {
      realPapers.value = papers
      if (papers.length > scanStartCount) {
        scanResult.value = { newCount: papers.length - scanStartCount }
        stopScan()
        return
      }
    }
    if (pollCount >= 11) {
      scanResult.value = { done: true }
      stopScan()
    }
  }, 8000)

  scanStopTimer = setTimeout(stopScan, 95000)
}

function stopScan() {
  scanning.value = false
  clearInterval(scanPollTimer)
  clearTimeout(scanStopTimer)
  scanPollTimer = null
  scanStopTimer = null
  setTimeout(() => { scanResult.value = null }, 10000)
}

const tooltip = reactive({ show: false, title: '', meta: '', left: 0, top: 0 })

const modal = reactive({
  tagText: '', tagBg: '', tagBorder: '', tagColor: '',
  title: '', auth: '', abs: '',
  airaLabel: '-', scoreColor: '', decision: '-', category: '-',
  mbarStyle: {},
  summ: '', pdfUrl: '', onOpenPaper: null
})

const activePaperIdx = ref(null)

function goToCategory(catName) {
  store.curCat = catName
  store.searchQuery = ''
  store.go('p2')
}

function sc(s) { return s >= 85 ? '#ff8c42' : s >= 70 ? '#ffb470' : 'rgba(140,160,200,0.7)' }
function scc(s) { return s >= 85 ? 'sh' : s >= 70 ? 'sm' : 'sl' }

// AIRA 5-tier helpers — threshold=5.0, 5 equal intervals up to 10
const ACCEPT_THRESHOLD = 5.0
const AIRA_TIER_COLORS = ['#4f8ef5', '#00d4aa', '#f59e0b', '#ff7b45', '#8b5cf6']
const AIRA_TIER_CLASSES = ['s-t1', 's-t2', 's-t3', 's-t4', 's-t5']

function _airaTierIdx(score) {
  if (score == null || score < ACCEPT_THRESHOLD) return -1
  const step = (10 - ACCEPT_THRESHOLD) / 5
  const idx = Math.floor((10 - score) / step)
  return Math.min(Math.max(idx, 0), 4)
}
function airaScc(score) {
  const i = _airaTierIdx(score)
  return i >= 0 ? AIRA_TIER_CLASSES[i] : 's-t0'
}
function airaScoreColor(score) {
  const i = _airaTierIdx(score)
  return i >= 0 ? AIRA_TIER_COLORS[i] : 'rgba(140,160,200,0.5)'
}
function airaTbarStyle(score) {
  const pct = score != null ? (score / 10 * 100) : 0
  return { width: pct + '%', background: airaScoreColor(score) }
}
function decisionColor(decision) {
  const map = {
    'Accept': '#4f8ef5',
    'Weak Accept': '#00d4aa',
    'Borderline': '#f59e0b',
    'Weak Reject': '#ff7b45',
    'Reject': '#8b5cf6',
  }
  return map[decision] || '#c8d4ff'
}

function openModal(idx) {
  activePaperIdx.value = idx
  const p = PP[idx], cl = CL[p.cl]
  modal.tagText = cl.name + ' · ' + p.venue
  modal.tagBg = cl.glow
  modal.tagBorder = `0.5px solid ${cl.color}55`
  modal.tagColor = cl.color
  modal.title = p.title
  modal.auth = p.auth
  modal.abs = p.abs
  modal.airaLabel = p.score + '/100'
  modal.scoreColor = sc(p.score)
  modal.decision = '-'
  modal.category = cl.name
  modal.mbarStyle = { width: p.score + '%', background: '#ff8c42', opacity: 0.75 }
  const mappedPaper = PAPERS[idx % PAPERS.length]
  modal.summ = fmtMd(mappedPaper.summ)
  modal.pdfUrl = ''
  modal.onOpenPaper = () => { closeModal(); store.openPaper(mappedPaper.id) }
  store.p1ModalOpen = true
  selIdx = idx
  redraw()
}

async function openRealModal(paper, idx) {
  activeRealIdx.value = idx
  modal.tagText = paper.metadata?.category || '-'
  modal.tagBg = 'rgba(79,142,245,0.15)'
  modal.tagBorder = '0.5px solid rgba(79,142,245,0.4)'
  modal.tagColor = '#4f8ef5'
  modal.title = paper.metadata?.title || paper.paper_id
  modal.auth = ''
  modal.abs = ''
  modal.airaLabel = paper.aira_score != null ? paper.aira_score.toFixed(1) : '-'
  modal.scoreColor = airaScoreColor(paper.aira_score)
  modal.decision = paper.metadata?.evaluation_decision || '-'
  modal.category = paper.metadata?.category || '-'
  modal.mbarStyle = airaTbarStyle(paper.aira_score)
  modal.summ = '<div style="color:var(--t3);font-size:12px">불러오는 중...</div>'
  modal.pdfUrl = ''
  modal.onOpenPaper = () => { closeModal(); goToCategory(paper.metadata?.category || '전체') }
  store.p1ModalOpen = true

  try {
    const detail = await fetchPaperById(paper.paper_id)
    let authors = []
    try { authors = JSON.parse(detail.authors || '[]') } catch {}
    modal.auth = authors.slice(0, 3).join(', ')
    modal.airaLabel = detail.aira_score != null ? detail.aira_score.toFixed(1) : '-'
    modal.scoreColor = airaScoreColor(detail.aira_score)
    modal.decision = detail.aira_decision || '-'
    modal.category = detail.category || paper.metadata?.category || '-'
    modal.mbarStyle = airaTbarStyle(detail.aira_score)
    modal.summ = fmtMd(detail.md_summary || '요약 없음')
    modal.pdfUrl = detail.paper_url || ''
    modal.onOpenPaper = () => { closeModal(); goToCategory(detail.category || paper.metadata?.category || '전체') }
  } catch (e) {
    modal.summ = '<div style="color:var(--t3)">상세 정보를 불러올 수 없습니다.</div>'
  }
}

function closeModal() {
  store.p1ModalOpen = false
  activePaperIdx.value = null
  activeRealIdx.value = null
  selIdx = null
  redraw()
}

// ── Canvas Viz ───────────────────────────────────────────────
let W = 0, H = 0, vctx = null
let selIdx = null, hovIdx = null, pCache = [], clCache = []
let rotX = 0.28, rotY = 0.52, zoom = 1.0
let dragging = false, lmx = 0, lmy = 0, vx2 = 0, vy2 = 0, dd = 0
let autoRotating = true, autoResumeTimer = null, animId = null

let _s = 42
function rng() { _s ^= _s << 13; _s ^= _s >> 17; _s ^= _s << 5; return (_s >>> 0) / 4294967296 }
function rn() { return Math.sqrt(-2 * Math.log(rng() + 1e-9)) * Math.cos(2 * Math.PI * rng()) }

const bgPts = []
CL.forEach((cl) => {
  for (let i = 0; i < 200; i++) {
    const sp = cl.r * 0.32
    bgPts.push({ x: cl.cx + rn() * sp, y: cl.cy + rn() * sp, z: cl.cz + rn() * sp * 0.7, ci: CL.indexOf(cl), sz: 1.2 + rng() * 1.6, a: 0.2 + rng() * 0.35 })
  }
})
const pPts = PP.map((p, i) => {
  const cl = CL[p.cl]; const ang = (i / PP.length) * Math.PI * 2
  return { x: cl.cx + Math.cos(ang) * 0.025, y: cl.cy + Math.sin(ang) * 0.025, z: cl.cz + 0.01, ci: p.cl, pi: i }
})

function proj(x, y, z) {
  const cx = Math.cos(rotX), sx = Math.sin(rotX), cy = Math.cos(rotY), sy = Math.sin(rotY)
  const y2 = y * cx - z * sx, z2 = y * sx + z * cx, x2 = x * cy + z2 * sy, z3 = -x * sy + z2 * cy
  const f = 1.4, s = f / (f + z3 + 0.6)
  return { sx: W / 2 + x2 * W * 0.65 * s * zoom, sy: H / 2 + y2 * H * 0.65 * s * zoom, s, z3 }
}

function redraw() {
  if (!vctx) return
  vctx.clearRect(0, 0, W, H)
  const bps = bgPts.map((p, i) => ({ p, pr: proj(p.x, p.y, p.z), t: 'b', i }))
  const vps = pPts.map((p, i) => ({ p, pr: proj(p.x, p.y, p.z), t: 'p', i }))
  pCache = vps
  clCache = CL.map((cl, i) => ({ pr: proj(cl.cx, cl.cy, cl.cz), i }))
  const drawn = new Set()
  PP.forEach((p, i) => {
    const sp = vps[i].pr
    p.rel.forEach(ri => {
      if (ri >= PP.length) return
      const key = Math.min(i, ri) + '-' + Math.max(i, ri)
      if (drawn.has(key)) return
      drawn.add(key)
      const rp = vps[ri].pr
      const isAct = (selIdx === i || selIdx === ri), isHovE = (hovIdx === i || hovIdx === ri)
      const g = vctx.createLinearGradient(sp.sx, sp.sy, rp.sx, rp.sy)
      if (isAct) { g.addColorStop(0, CL[PP[i].cl].color + 'ee'); g.addColorStop(1, CL[PP[ri].cl].color + 'aa'); vctx.lineWidth = 1.5 }
      else if (isHovE) { g.addColorStop(0, CL[PP[i].cl].color + '88'); g.addColorStop(1, CL[PP[ri].cl].color + '55'); vctx.lineWidth = 0.9 }
      else { g.addColorStop(0, CL[PP[i].cl].color + '99'); g.addColorStop(1, CL[PP[ri].cl].color + '66'); vctx.lineWidth = 1.0 }
      vctx.beginPath(); vctx.moveTo(sp.sx, sp.sy); vctx.lineTo(rp.sx, rp.sy)
      vctx.strokeStyle = g; vctx.stroke(); vctx.setLineDash([])
    })
  })
  ;[...bps, ...vps].sort((a, b) => a.pr.z3 - b.pr.z3).forEach(({ p, pr, t, i }) => {
    const cl = CL[p.ci]
    if (t === 'b') {
      const s = Math.max(0.6, (p.sz * pr.s * Math.min(W, H)) / 600)
      vctx.beginPath(); vctx.arc(pr.sx, pr.sy, s, 0, Math.PI * 2)
      vctx.fillStyle = cl.color + Math.round(p.a * 255).toString(16).padStart(2, '0'); vctx.fill()
    } else {
      const isSel = selIdx === i, isHov = hovIdx === i, isRel = selIdx !== null && PP[selIdx].rel.includes(i)
      const base = (pr.s * Math.min(W, H)) / 30, r = isSel ? base * 2.0 : isHov ? base * 1.6 : base
      const grd = vctx.createRadialGradient(pr.sx, pr.sy, 0, pr.sx, pr.sy, r * 3.0)
      grd.addColorStop(0, cl.color + (isSel ? '55' : isHov ? '33' : '1a')); grd.addColorStop(1, cl.color + '00')
      vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r * 3.0, 0, Math.PI * 2); vctx.fillStyle = grd; vctx.fill()
      vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r, 0, Math.PI * 2); vctx.fillStyle = cl.color + (isSel ? '18' : isHov ? '12' : '0a'); vctx.fill()
      vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r, 0, Math.PI * 2)
      vctx.strokeStyle = cl.color + (isSel ? 'ff' : isHov ? 'ff' : isRel ? 'dd' : 'bb')
      vctx.lineWidth = isSel ? 2.8 : isHov ? 2.2 : 1.6; vctx.stroke()
      if (isSel) {
        vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r + 6, 0, Math.PI * 2); vctx.strokeStyle = cl.color + '44'; vctx.lineWidth = 1; vctx.stroke()
        vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r + 11, 0, Math.PI * 2); vctx.strokeStyle = cl.color + '1a'; vctx.lineWidth = 0.8; vctx.stroke()
      }
      vctx.beginPath(); vctx.arc(pr.sx, pr.sy, r * 0.16, 0, Math.PI * 2)
      vctx.fillStyle = isSel ? '#fff' : cl.color; vctx.fill()
      if (isHov || isSel) {
        vctx.font = '500 10px "DM Sans",sans-serif'; vctx.fillStyle = cl.color; vctx.textAlign = 'center'
        vctx.fillText(PP[i].venue + ' · ' + PP[i].score, pr.sx, pr.sy - r - 8); vctx.textAlign = 'left'
      }
    }
  })
}

function resizeV() {
  const lp = leftPanelRef.value
  const vc = vizCanvasRef.value
  if (!lp || !vc) return
  W = lp.offsetWidth; H = lp.offsetHeight; vc.width = W; vc.height = H; redraw()
}

onMounted(() => {
  // Background canvas
  const bgC = bgCanvasRef.value
  const bgX = bgC.getContext('2d')
  function resizeBg() {
    bgC.width = window.innerWidth; bgC.height = window.innerHeight
    bgX.fillStyle = '#03060e'; bgX.fillRect(0, 0, bgC.width, bgC.height)
    const w = bgC.width, h = bgC.height
    const b1 = bgX.createRadialGradient(w * 0.15, h * 0.2, 0, w * 0.15, h * 0.2, w * 0.65)
    b1.addColorStop(0, 'rgba(18,50,170,0.28)'); b1.addColorStop(1, 'rgba(2,6,15,0)')
    bgX.fillStyle = b1; bgX.fillRect(0, 0, w, h)
    const b2 = bgX.createRadialGradient(w * 0.85, h * 0.8, 0, w * 0.85, h * 0.8, w * 0.5)
    b2.addColorStop(0, 'rgba(15,40,150,0.22)'); b2.addColorStop(1, 'rgba(2,6,15,0)')
    bgX.fillStyle = b2; bgX.fillRect(0, 0, w, h)
    const o1 = bgX.createRadialGradient(w * 0.82, h * 0.12, 0, w * 0.82, h * 0.12, w * 0.28)
    o1.addColorStop(0, 'rgba(255,100,30,0.10)'); o1.addColorStop(1, 'rgba(2,6,15,0)')
    bgX.fillStyle = o1; bgX.fillRect(0, 0, w, h)
  }
  resizeBg()
  window.addEventListener('resize', resizeBg)

  // Viz canvas
  const vc = vizCanvasRef.value
  vctx = vc.getContext('2d')

  vc.addEventListener('wheel', e => {
    e.preventDefault()
    zoom = Math.min(4, Math.max(0.3, zoom * (e.deltaY < 0 ? 1.1 : 0.91)))
    redraw()
  }, { passive: false })

  let lastPinchDist = null
  vc.addEventListener('touchstart', e => { if (e.touches.length === 2) lastPinchDist = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY) }, { passive: true })
  vc.addEventListener('touchmove', e => {
    if (e.touches.length === 2 && lastPinchDist) {
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY)
      zoom = Math.min(4, Math.max(0.3, zoom * (d / lastPinchDist))); lastPinchDist = d; redraw()
    }
  }, { passive: true })
  vc.addEventListener('touchend', () => { lastPinchDist = null }, { passive: true })

  vc.addEventListener('mousedown', e => { dragging = true; dd = 0; lmx = e.clientX; lmy = e.clientY; vx2 = 0; vy2 = 0; isDragging.value = true; autoRotating = false; if (autoResumeTimer) clearTimeout(autoResumeTimer) })
  window.addEventListener('mouseup', () => {
    if (!dragging) return; dragging = false; isDragging.value = false
    autoResumeTimer = setTimeout(() => { autoRotating = true }, 1800)
  })
  window.addEventListener('mousemove', e => {
    if (dragging) {
      const dx = e.clientX - lmx, dy = e.clientY - lmy
      dd += Math.abs(dx) + Math.abs(dy); vy2 = dx * 0.008; vx2 = dy * 0.008
      rotY += vy2; rotX += vx2; lmx = e.clientX; lmy = e.clientY; redraw(); return
    }
    const rect = vc.getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    let near = null, nd = 28
    pCache.forEach(({ pr, i }) => { const d = Math.hypot(pr.sx - mx, pr.sy - my); if (d < nd) { nd = d; near = i } })
    if (near !== hovIdx) { hovIdx = near; redraw() }
    if (near !== null) {
      tooltip.title = CL[PP[near].cl].name
      tooltip.meta = ''
      tooltip.left = Math.min(mx + 13, W - 190)
      tooltip.top = Math.max(my - 58, 8)
      tooltip.show = true
    } else { tooltip.show = false }
  })
  vc.addEventListener('mouseleave', () => { hovIdx = null; tooltip.show = false; redraw() })
  vc.addEventListener('click', e => {
    if (dd > 6) return
    const rect = vc.getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    let nearCl = null, ndCl = 80
    clCache.forEach(({ pr, i }) => { const d = Math.hypot(pr.sx - mx, pr.sy - my); if (d < ndCl) { ndCl = d; nearCl = i } })
    if (nearCl !== null) goToCategory(CL[nearCl].name)
  })

  function loop() {
    if (!dragging && autoRotating) { rotY += 0.0018; redraw() }
    else if (!dragging && (Math.abs(vx2) > 0.0001 || Math.abs(vy2) > 0.0001)) { rotX += vx2; rotY += vy2; vx2 *= 0.92; vy2 *= 0.92; redraw() }
    animId = requestAnimationFrame(loop)
  }
  loop()

  resizeV()
  window.addEventListener('resize', resizeV)

  // Fetch real papers from paper-service
  realPapersLoading.value = true
  fetchPapers(15).then(data => {
    realPapers.value = data
  }).catch(() => {
    realPapers.value = []
  }).finally(() => {
    realPapersLoading.value = false
  })

  // 30초마다 자동 갱신
  pollTimer = setInterval(() => {
    fetchPapers(15).then(data => { realPapers.value = data }).catch(() => {})
  }, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (researchPollTimer) clearInterval(researchPollTimer)
  stopScan()
  if (animId) cancelAnimationFrame(animId)
  window.removeEventListener('resize', resizeV)
})
</script>

<style scoped>
@keyframes scan-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,.5); }
  50%       { box-shadow: 0 0 12px 4px rgba(37,99,235,.15); }
}
@keyframes dot-blink {
  0%, 80%, 100% { opacity: .2; }
  40%           { opacity: 1; }
}
@keyframes live-dot {
  0%, 100% { transform: scale(1); opacity: .8; }
  50%      { transform: scale(1.5); opacity: .3; }
}

.scan-btn.loading { animation: scan-pulse 1.5s ease infinite; }

.scan-live-banner {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; color: rgba(147,197,253,.85);
  padding: 6px 12px; margin-top: 6px;
  background: rgba(37,99,235,.1);
  border: 1px solid rgba(37,99,235,.2);
  border-radius: 8px;
}
.scan-live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #3b82f6;
  animation: live-dot 1.2s ease infinite;
}
.scan-dots span { animation: dot-blink 1.4s infinite; }
.scan-dots span:nth-child(2) { animation-delay: .2s; }
.scan-dots span:nth-child(3) { animation-delay: .4s; }

.research-btn {
  padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 600;
  background: rgba(0,212,170,.15); color: #00d4aa;
  border: 1px solid rgba(0,212,170,.3); cursor: pointer; transition: all .15s;
}
.research-btn:hover { background: rgba(0,212,170,.28); }
.research-panel {
  position: absolute; inset: 0; background: rgba(3,6,14,.97);
  backdrop-filter: blur(24px); z-index: 20;
  display: flex; flex-direction: column; gap: 10px;
  padding: 14px 14px 10px; overflow-y: auto;
}
.research-header { display: flex; align-items: center; justify-content: space-between; }
.research-title { font-size: 13px; font-weight: 600; color: rgba(210,220,255,.9); }
.research-close { background: none; border: none; color: rgba(180,200,255,.5); font-size: 16px; cursor: pointer; }
.research-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 11px; color: rgba(160,180,230,.6); }
.rdate-in { background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); border-radius: 6px; padding: 4px 8px; font-size: 11px; color: rgba(210,220,255,.9); font-family: inherit; }
.rcat-chips { display: flex; gap: 5px; flex-wrap: wrap; }
.rcat-chip { padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 600; border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.05); color: rgba(180,200,255,.7); cursor: pointer; transition: all .15s; }
.rcat-chip.on { background: rgba(37,99,235,.35); border-color: rgba(37,99,235,.6); color: #93c5fd; }
.rkw-in { flex: 1; min-width: 140px; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.1); border-radius: 6px; padding: 5px 9px; font-size: 11px; color: rgba(210,220,255,.9); font-family: inherit; outline: none; }
.research-go-btn { padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; background: rgba(37,99,235,.5); color: #dde5ff; border: none; cursor: pointer; transition: all .15s; }
.research-go-btn:hover:not(:disabled) { background: rgba(37,99,235,.75); }
.research-go-btn:disabled { opacity: .5; cursor: not-allowed; }
.research-loading { display: flex; align-items: center; gap: 7px; font-size: 11px; color: rgba(147,197,253,.8); padding: 8px 0; }
.research-spinner { width: 14px; height: 14px; border: 2px solid rgba(37,99,235,.3); border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.research-result-count { font-size: 11px; color: rgba(0,212,170,.8); font-weight: 600; padding: 4px 0; }
.research-results { display: flex; flex-direction: column; gap: 7px; }
.research-paper-item { background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.07); border-radius: 8px; padding: 10px 12px; }
.rp-title { font-size: 12px; font-weight: 600; color: rgba(210,220,255,.9); margin-bottom: 4px; line-height: 1.4; }
.rp-meta { display: flex; gap: 8px; font-size: 10px; color: rgba(140,160,210,.6); margin-bottom: 5px; }
.rp-abs { font-size: 11px; color: rgba(160,180,230,.6); line-height: 1.6; }
.research-pipeline-badge {
  font-size: 10px; color: rgba(0,212,170,.75); font-weight: 600;
  background: rgba(0,212,170,.08); border: 1px solid rgba(0,212,170,.2);
  border-radius: 6px; padding: 5px 10px; margin-top: 2px;
}
</style>
