<template>
  <div id="p1" class="page">
    <canvas ref="bgCanvasRef" id="bgCanvas"></canvas>
    <div class="p1-body">
      <div class="p1-left" ref="leftPanelRef">
        <canvas ref="vizCanvasRef" id="vizCanvas" :class="{ drag: isDragging }"></canvas>
        <div class="viz-info">드래그로 회전 · 스크롤로 확대/축소 · 클릭으로 논문 선택</div>
        <!-- Automated Reviewer Panel -->
        <div class="reviewer-panel" @click="store.go('p6')">
          <div class="rp-title">Automated Reviewer</div>
          <div class="rp-desc">3인 심사 앙상블<br>+ 반성 루프 + Area Chair</div>
          <div class="rp-score-row">
            <span class="rp-badge accept">≥ 6.0 Accept</span>
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
                <div class="modal-stat-value" style="color:#c8d4ff;font-size:11px">{{ modal.decision }}</div>
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

      <div class="p1-right">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <div class="p1-sec-title">최신 논문</div>
          <div class="p1-badge">실시간</div>
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
import { store } from '../store.js'
import { PP, CL } from '../data/vizData.js'
import { PAPERS } from '../data/papers.js'
import { fmtMd } from '../utils/format.js'
import { fetchPapers, fetchPaperById } from '../api/paperService.js'

const bgCanvasRef = ref(null)
const vizCanvasRef = ref(null)
const leftPanelRef = ref(null)
const isDragging = ref(false)

const realPapers = ref([])
const realPapersLoading = ref(false)
const activeRealIdx = ref(null)

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

// AIRA Score helpers
function airaScc(score) {
  if (score == null) return 'sl'
  return score >= 7 ? 'sh' : score >= 6 ? 'sm' : 'sl'
}
function airaTbarStyle(score) {
  const pct = score != null ? (score / 10 * 100) : 0
  const color = score != null && score >= 6 ? '#4f8ef5' : 'rgba(140,160,200,0.4)'
  return { width: pct + '%', background: color }
}
function airaScoreColor(score) {
  if (score == null) return 'rgba(140,160,200,0.7)'
  return score >= 7 ? '#ff8c42' : score >= 6 ? '#ffb470' : 'rgba(140,160,200,0.7)'
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
  modal.onOpenPaper = null
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
    modal.onOpenPaper = detail.paper_url ? () => { window.open(detail.paper_url, '_blank') } : null
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
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  window.removeEventListener('resize', resizeV)
})
</script>
