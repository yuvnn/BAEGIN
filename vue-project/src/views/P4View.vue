<template>
  <div ref="rootEl" class="dashboard-root">
    <canvas ref="bgCanvasEl" class="bg-canvas"></canvas>

    <div class="topbar">
      <div class="logo">Bea<span>gin</span></div>
      <div class="tabs">
        <button class="tab active" type="button">탐색</button>
        <button class="tab" type="button">신뢰 평가</button>
        <button class="tab" type="button">보고서</button>
        <button class="tab" type="button">아카이브</button>
      </div>
      <div style="display:flex;align-items:center;gap:8px;">
        <div class="searchbox">논문 검색...</div>
      </div>
    </div>

    <div class="body">
      <div class="compare-left">
        <div class="compare-left-header">
          <span class="compare-label">사내 비교 문서</span>
          <div class="compare-actions">
            <button class="compare-act-btn" type="button" :disabled="reportLoading" @click="runFixedCompare">
              {{ reportLoading ? "생성 중..." : "재생성하기" }}
            </button>
            <button class="compare-act-btn" type="button">내보내기 ↗</button>
            <button class="compare-act-btn sec" type="button">저장</button>
          </div>
        </div>

        <div class="compare-doc-area">
          <div class="compare-doc-scroll">
            <div class="rpt-overview">
              <div class="rpt-overview-title">논문-기획서 비교 분석 보고서</div>
              <div class="rpt-overview-meta">
                <span class="rpt-meta-chip">dynamic report</span>
                <span class="rpt-meta-chip chip-internal">internal-service latest</span>
                <span class="rpt-meta-date">{{ latestReport?.updated_at || "-" }}</span>
              </div>
              <div class="rpt-summary">{{ reportSections.overview_summary || fallbackOverview }}</div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">01</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">기획서 핵심 요구사항 <span :class="['sec-state', sectionStatuses.internal_requirements_3lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.internal_requirements_3lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('internal_requirements_3lines') }]">
                  <div
                    v-for="(line, idx) in internalRequirementLines"
                    :key="`internal-req-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `internal_requirements_3lines-${idx}` }]"
                    @click="openCitationFromSection('internal_requirements_3lines', idx)"
                  >
                    <span class="bul-dot"></span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">02</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">논문 핵심 기술 요약 <span :class="['sec-state', sectionStatuses.paper_tech_summary_3lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.paper_tech_summary_3lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('paper_tech_summary_3lines') }]">
                  <div
                    v-for="(line, idx) in paperTechLines"
                    :key="`paper-tech-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `paper_tech_summary_3lines-${idx}` }]"
                    @click="openCitationFromSection('paper_tech_summary_3lines', idx)"
                  >
                    <span class="bul-dot bul-blue"></span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">03</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">기획서-논문 매핑 분석 (raw) <span :class="['sec-state', sectionStatuses.mapping_analysis_table_md === 'completed' ? 'done' : 'run']">{{ sectionStatuses.mapping_analysis_table_md === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div v-if="mappingTableRows.length > 0" :class="['mapping-table-wrap', { 'section-glass-loading': isSectionLoading('mapping_analysis_table_md') }]">
                  <table class="mapping-table">
                    <colgroup>
                      <col
                        v-for="(header, idx) in mappingTableHeaders"
                        :key="`mapping-col-${idx}`"
                        :class="mappingColClass(header)"
                      />
                    </colgroup>
                    <thead>
                      <tr>
                        <th v-for="(header, idx) in mappingTableHeaders" :key="`mapping-header-${idx}`">{{ header }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rowIdx) in mappingTableRows" :key="`mapping-row-${rowIdx}`">
                        <td v-for="(cell, cellIdx) in row" :key="`mapping-cell-${rowIdx}-${cellIdx}`">{{ cell }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <pre v-else :class="['json-report-pre', { 'section-glass-loading': isSectionLoading('mapping_analysis_table_md') }]">{{ reportSections.mapping_analysis_table_md || "" }}</pre>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">04</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">접목 가능한 기술 후보 <span :class="['sec-state', sectionStatuses.candidate_technologies_10lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.candidate_technologies_10lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('candidate_technologies_10lines') }]">
                  <div
                    v-for="(line, idx) in candidateTechLines"
                    :key="`candidate-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `candidate_technologies_10lines-${idx}` }]"
                    @click="openCitationFromSection('candidate_technologies_10lines', idx)"
                  >
                    <span class="bul-idx">{{ idx + 1 }}</span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">05</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">도입 방식 설계 <span :class="['sec-state', sectionStatuses.integration_design_10lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.integration_design_10lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('integration_design_10lines') }]">
                  <div
                    v-for="(line, idx) in integrationDesignLines"
                    :key="`integration-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `integration_design_10lines-${idx}` }]"
                    @click="openCitationFromSection('integration_design_10lines', idx)"
                  >
                    <span class="bul-idx">{{ idx + 1 }}</span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">06</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">기대 효과 <span :class="['sec-state', sectionStatuses.expected_impact_5lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.expected_impact_5lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('expected_impact_5lines') }]">
                  <div
                    v-for="(line, idx) in expectedImpactLines"
                    :key="`impact-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `expected_impact_5lines-${idx}` }]"
                    @click="openCitationFromSection('expected_impact_5lines', idx)"
                  >
                    <span class="bul-dot bul-orange"></span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section">
              <div class="rpt-sec-num">07</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">한계와 리스크 <span :class="['sec-state', sectionStatuses.limitations_and_risks_5lines === 'completed' ? 'done' : 'run']">{{ sectionStatuses.limitations_and_risks_5lines === 'completed' ? '완료' : '생성 중' }}</span></div>
                <div :class="['rpt-bullets', { 'section-glass-loading': isSectionLoading('limitations_and_risks_5lines') }]">
                  <div
                    v-for="(line, idx) in limitationRiskLines"
                    :key="`risk-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `limitations_and_risks_5lines-${idx}` }]"
                    @click="openCitationFromSection('limitations_and_risks_5lines', idx)"
                  >
                    <span class="bul-dot bul-red"></span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="rpt-section rpt-last">
              <div class="rpt-sec-num">08</div>
              <div class="rpt-sec-content">
                <div class="rpt-sec-title">종합 결론 및 우선순위</div>
                <div class="rpt-bullets">
                  <div
                    v-for="(line, idx) in finalConclusionLines"
                    :key="`final-${idx}`"
                    :class="['rpt-bullet', 'linkable', { 'active-link': activeLink === `final_conclusion_and_priorities_5lines-${idx}` }]"
                    @click="openCitationFromSection('final_conclusion_and_priorities_5lines', idx)"
                  >
                    <span class="bul-dot bul-blue"></span>
                    {{ line }}
                    <span class="link-arrow">↗ 근거 보기</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="compare-right">
        <div class="doc-tabs">
          <button :class="['doc-tab', { active: activeTab === '사내문서' }]" type="button" @click="switchTab('사내문서')">사내문서</button>
          <button :class="['doc-tab', { active: activeTab === '논문요약' }]" type="button" @click="switchTab('논문요약')">논문요약</button>
          <button :class="['doc-tab', { active: activeTab === '논문원문' }]" type="button" @click="switchTab('논문원문')">논문원문</button>
        </div>

        <div class="doc-viewer">
          <div class="doc-content">
            <div class="doc-meta">
              <span class="doc-meta-tag">{{ activeTab }}</span>
              <span class="doc-meta-date">anchor: {{ viewerCitation?.anchor || '-' }}</span>
              <span class="doc-meta-author">source_type: {{ viewerCitation?.source_type || '-' }}</span>
            </div>

            <div class="doc-title-big">Citation Source Viewer</div>
            <div class="doc-subtitle">탭별 원문/요약 렌더링 + citation 하이라이트</div>

            <div class="doc-body-text" v-if="activeTab === '논문요약'">
              <div v-if="paperSummaryHtml" class="md-render" v-html="paperSummaryHtml"></div>
              <p v-else>논문 요약 데이터가 없습니다.</p>
            </div>

            <div class="doc-body-text" v-else-if="activeTab === '논문원문'">
              <div v-if="paperOriginalUrl">
                <a :href="paperOriginalUrl" target="_blank" rel="noopener" class="paper-open-btn">
                  📄 논문 원문 새 탭에서 열기 ↗
                </a>
                <p class="paper-iframe-notice">※ 일부 논문 사이트는 브라우저 보안 정책으로 인해 직접 표시가 제한될 수 있습니다.</p>
                <div class="doc-embed-wrap" style="margin-top:12px;">
                  <iframe :src="paperOriginalUrl" class="doc-embed-frame" title="Paper Original PDF" loading="lazy"></iframe>
                </div>
              </div>
              <p v-else>paper_url 정보가 없어 논문 원문을 열 수 없습니다.</p>
            </div>

            <div class="doc-body-text" v-else>
              <div v-if="hasPdfDoc" class="doc-embed-wrap">
                <iframe :src="internalPdfUrl" class="doc-embed-frame" title="사내문서 PDF" loading="lazy"></iframe>
              </div>
              <div v-else-if="internalDocText" class="internal-doc-text">{{ internalDocText }}</div>
              <p v-else style="color:#6688aa;font-size:14px;">사내문서 내용을 불러올 수 없습니다.</p>
            </div>

            <div class="rpt-overview" style="padding:12px;margin-top:12px;">
              <div class="rpt-sec-title">citation 목록</div>
              <div class="rpt-bullets">
                <div
                  v-for="(c, idx) in citationList"
                  :key="`citation-${c.citation_id}-${idx}`"
                  class="rpt-bullet linkable"
                  @click="openCitation(c)"
                >
                  <span class="bul-dot" :class="c.source_type === 'paper' ? 'bul-blue' : ''"></span>
                  [{{ c.source_type }}] {{ readableCitationLabel(c, idx) }}
                </div>
                <div v-if="citationList.length === 0" class="rpt-bullet">citation 데이터 없음</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { getReportStreamUrl, startReportGeneration, getReportById, getInternalDocText, listInternalDocs, getReportList } from "../api/reportService";
import { fetchPaperById } from "../api/paperService";
import { store } from "../store.js";

const rootEl = ref(null);
const bgCanvasEl = ref(null);
const activeTab = ref("사내문서");
const activeLink = ref("");
const latestReport = ref(null);
const internalDocText = ref("");
const paperSummaryMd = ref("");
const reportLoading = ref(false);
const reportError = ref("");
const activeCitation = ref(null);
const sectionStatuses = ref({
  internal_requirements_3lines: "pending",
  paper_tech_summary_3lines: "pending",
  mapping_analysis_table_md: "pending",
  candidate_technologies_10lines: "pending",
  integration_design_10lines: "pending",
  expected_impact_5lines: "pending",
  limitations_and_risks_5lines: "pending",
  final_conclusion_and_priorities_5lines: "pending",
});

const FIXED_PAPER_ID = "paper-demo-001";
const activeInternalDoc = ref(null); // { doc_id, source_file, title } — API에서 동적 로드
const DUMMY_PAPER_ORIGINAL_URL = "https://arxiv.org/pdf/2604.08626";
const DUMMY_PAPER_SUMMARY_MD = `## 문제 정의

3D 객체 인식은 공간 지능의 핵심 요소로, 단일 이미지에서 객체의 위치, 크기 및 방향을 복구하는 단안 3D 객체 검출이 중요합니다. 기존 방법은 단일 프롬프트 유형에 최적화되어 추가 기하 단서 통합이 어렵고, 데이터셋 범위가 좁아 개방형 세계 일반화 한계가 있습니다.

## 연구 방법론

- WildDet3D 아키텍처: 텍스트, 포인트, 박스 프롬프트를 통합 지원하고 추론 시 보조 깊이 신호를 결합합니다.
- WildDet3D-Data: 13,500+ 범주, 100만+ 이미지의 대규모 개방형 3D 검출 데이터셋을 구축했습니다.
- 입력 모달리티: RGB + 선택적 깊이 입력으로 개방형 어휘 인식을 유지하면서 스케일 모호성을 줄였습니다.

## 주요 실험 결과

개방형 세계 벤치마크에서 SOTA를 달성했고, 깊이 단서 결합 시 평균 +20.7 AP 향상을 기록했습니다.

## 핵심 기여 및 의의

- 통합 프롬프트 지원
- 대규모 인간 검증 데이터셋
- 깊이 신호 기반 정확도 개선

## 한계점 및 향후 연구

- 깊이 신호 의존성
- 데이터 편향 가능성
- 실시간 처리 최적화 필요`;

const defaultCitations = computed(() => {
  const list = [
    {
      citation_id: "fallback-paper-1",
      source_type: "paper",
      source_id: FIXED_PAPER_ID,
      source_text: DUMMY_PAPER_SUMMARY_MD,
      text_quote: null,
      char_start: null,
      char_end: null,
      anchor: "paper_tech_1",
      metadata: {
        title: "WildDet3D: Open-Vocabulary Monocular 3D Object Detection in the Wild",
        paper_url: DUMMY_PAPER_ORIGINAL_URL,
        category: "ML Foundation",
      },
    },
  ];
  if (activeInternalDoc.value) {
    list.push({
      citation_id: "fallback-internal-1",
      source_type: "internal",
      source_id: activeInternalDoc.value.doc_id,
      source_text: "-",
      text_quote: null,
      char_start: null,
      char_end: null,
      anchor: "int_req_1",
      metadata: {
        title: activeInternalDoc.value.title || "",
        doc_id: activeInternalDoc.value.doc_id,
        source_file: activeInternalDoc.value.source_file || "",
        source_ext: ".pdf",
      },
    });
  }
  return list;
});
let resizeHandler = null;
let eventSource = null;
let lastStreamEventAt = 0;
let streamDisconnectCount = 0;
let streamCompleted = false;

const STREAM_SECTION_CODES = [
  "internal_requirements_3lines",
  "paper_tech_summary_3lines",
  "mapping_analysis_table_md",
  "candidate_technologies_10lines",
  "integration_design_10lines",
  "expected_impact_5lines",
  "limitations_and_risks_5lines",
  "final_conclusion_and_priorities_5lines",
];

const SKELETON_SECTION_CODES = [
  "internal_requirements_3lines",
  "paper_tech_summary_3lines",
  "mapping_analysis_table_md",
  "candidate_technologies_10lines",
  "integration_design_10lines",
  "expected_impact_5lines",
  "limitations_and_risks_5lines",
];

const fallbackOverview = "최신 리포트가 없어서 기본 화면을 표시합니다.";
const citationList = computed(() => {
  const fromReport = latestReport.value?.citations || [];
  return fromReport.length > 0 ? fromReport : defaultCitations.value;
});

const reportSections = computed(() => {
  return (
    latestReport.value?.report?.sections || {
      overview_summary: "",
      internal_requirements_3lines: "",
      paper_tech_summary_3lines: "",
      mapping_analysis_table_md: "",
      candidate_technologies_10lines: "",
      integration_design_10lines: "",
      expected_impact_5lines: "",
      limitations_and_risks_5lines: "",
      final_conclusion_and_priorities_5lines: "",
    }
  );
});

function resetSectionStatuses() {
  sectionStatuses.value = {
    internal_requirements_3lines: "pending",
    paper_tech_summary_3lines: "pending",
    mapping_analysis_table_md: "pending",
    candidate_technologies_10lines: "pending",
    integration_design_10lines: "pending",
    expected_impact_5lines: "pending",
    limitations_and_risks_5lines: "pending",
    final_conclusion_and_priorities_5lines: "pending",
  };
}

function isSectionLoading(sectionCode) {
  if (!SKELETON_SECTION_CODES.includes(sectionCode)) return false;
  return sectionStatuses.value[sectionCode] !== "completed";
}

function makeEmptyReport(reportId) {
  return {
    report_id: reportId,
    paper_id: FIXED_PAPER_ID,
    internal_doc_id: activeInternalDoc.value?.doc_id || null,
    status: "running",
    report: {
      title: "논문-기획서 비교 분석 보고서",
      sections: {
        overview_summary: "",
        internal_requirements_3lines: "",
        paper_tech_summary_3lines: "",
        mapping_analysis_table_md: "",
        candidate_technologies_10lines: "",
        integration_design_10lines: "",
        expected_impact_5lines: "",
        limitations_and_risks_5lines: "",
        final_conclusion_and_priorities_5lines: "",
      },
    },
    citations: [],
  };
}

function closeEventSource() {
  if (!eventSource) return;
  eventSource.close();
  eventSource = null;
}

function markStreamAlive() {
  lastStreamEventAt = Date.now();
  streamDisconnectCount = 0;
}

function updateSectionStatus(sectionCode, status) {
  sectionStatuses.value = {
    ...sectionStatuses.value,
    [sectionCode]: status,
  };
}

function applySectionUpdate(payload) {
  const sectionCode = payload?.section_code;
  if (!sectionCode) return;

  updateSectionStatus(sectionCode, payload.status || "running");
  if (payload.status === "completed" && latestReport.value?.report?.sections) {
    latestReport.value.report.sections[sectionCode] = payload.content || "";
  }
}

function completeAllSectionStatuses() {
  const next = { ...sectionStatuses.value };
  STREAM_SECTION_CODES.forEach((sectionCode) => {
    next[sectionCode] = "completed";
  });
  sectionStatuses.value = next;
}

function openSectionStream(reportId) {
  lastStreamEventAt = Date.now();
  streamDisconnectCount = 0;
  streamCompleted = false;
  eventSource = new EventSource(getReportStreamUrl(reportId));

  eventSource.addEventListener("section_update", (event) => {
    try {
      applySectionUpdate(JSON.parse(event.data || "{}"));
      reportError.value = "";
      markStreamAlive();
    } catch {
      // Ignore malformed payload.
    }
  });

  eventSource.addEventListener("completed", (event) => {
    try {
      const payload = JSON.parse(event.data || "{}");
      if (payload?.report) {
        latestReport.value = payload.report;
      }
      completeAllSectionStatuses();
      streamCompleted = true;
      reportError.value = "";
      markStreamAlive();
    } catch {
      // Ignore malformed payload.
    } finally {
      reportLoading.value = false;
      closeEventSource();
    }
  });

  eventSource.addEventListener("failed", (event) => {
    try {
      const payload = JSON.parse(event.data || "{}");
      reportError.value = payload?.message || "보고서 생성에 실패했습니다.";
      markStreamAlive();
    } catch {
      reportError.value = "보고서 생성에 실패했습니다.";
    } finally {
      reportLoading.value = false;
      closeEventSource();
    }
  });

  eventSource.onerror = () => {
    if (!reportLoading.value || streamCompleted) return;

    // Browser emits onerror during normal SSE auto-reconnect.
    if (eventSource && eventSource.readyState === EventSource.CONNECTING) {
      return;
    }

    streamDisconnectCount += 1;
    const elapsedMs = Date.now() - lastStreamEventAt;

    // Show error only when stream is truly stalled for a long time.
    if (streamDisconnectCount < 20 || elapsedMs < 180000) {
      return;
    }

    reportError.value = "스트림 연결이 끊겼습니다. 다시 시도해 주세요.";
    reportLoading.value = false;
    closeEventSource();
  };
}

function parseLineList(raw) {
  if (!raw || typeof raw !== "string") return [];
  return raw
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => v.replace(/^[-*]\s+/, "").trim());
}

const internalRequirementLines = computed(() => parseLineList(reportSections.value.internal_requirements_3lines));
const paperTechLines = computed(() => parseLineList(reportSections.value.paper_tech_summary_3lines));
const candidateTechLines = computed(() => parseLineList(reportSections.value.candidate_technologies_10lines));
const integrationDesignLines = computed(() => parseLineList(reportSections.value.integration_design_10lines));
const expectedImpactLines = computed(() => parseLineList(reportSections.value.expected_impact_5lines));
const limitationRiskLines = computed(() => parseLineList(reportSections.value.limitations_and_risks_5lines));
const finalConclusionLines = computed(() => parseLineList(reportSections.value.final_conclusion_and_priorities_5lines));

function parseMarkdownTable(raw) {
  if (!raw || typeof raw !== "string") return { headers: [], rows: [] };

  const lines = raw
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|") && line.endsWith("|"));

  if (lines.length < 2) return { headers: [], rows: [] };

  const toCells = (line) =>
    line
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());

  const headers = toCells(lines[0]).filter((cell) => cell.length > 0);
  if (headers.length === 0) return { headers: [], rows: [] };

  const isSeparatorRow = (cells) =>
    cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.replace(/\s+/g, "")));

  const secondLineCells = toCells(lines[1]);
  const dataStartIndex = isSeparatorRow(secondLineCells) ? 2 : 1;

  const rows = lines
    .slice(dataStartIndex)
    .map((line) => toCells(line))
    .filter((cells) => cells.some((cell) => cell.length > 0))
    .map((cells) => {
      if (cells.length < headers.length) {
        return [...cells, ...Array(headers.length - cells.length).fill("")];
      }
      return cells.slice(0, headers.length);
    });

  return { headers, rows };
}

const mappingTable = computed(() => parseMarkdownTable(reportSections.value.mapping_analysis_table_md));
const mappingTableHeaders = computed(() => mappingTable.value.headers);
const mappingTableRows = computed(() => mappingTable.value.rows);

function mappingColClass(header) {
  const normalized = String(header || "").replace(/\s+/g, "").toLowerCase();
  if (normalized.includes("기술id")) return "col-tech-id";
  if (normalized.includes("적합도")) return "col-score";
  if (normalized.includes("요구사항") && !normalized.includes("id")) return "col-requirement";
  return "";
}

const sectionAnchorSeeds = {
  internal_requirements_3lines: "int_req_",
  paper_tech_summary_3lines: "paper_tech_",
  candidate_technologies_10lines: "cand_",
  integration_design_10lines: "design_",
  expected_impact_5lines: "impact_",
  limitations_and_risks_5lines: "risk_",
  final_conclusion_and_priorities_5lines: "final_",
};

const sectionSourceHint = {
  internal_requirements_3lines: "internal",
  paper_tech_summary_3lines: "paper",
};

function resolveAnchor(sectionKey, idx) {
  const seed = sectionAnchorSeeds[sectionKey];
  if (!seed) return null;
  return `${seed}${idx + 1}`;
}

function openCitation(citation) {
  if (!citation) return;
  activeCitation.value = citation;
  if (citation.source_type === "internal") activeTab.value = "사내문서";
  if (citation.source_type === "paper") activeTab.value = "논문요약";
}

function findBestCitationForLine(sectionKey, idx, lineText) {
  const guessed = resolveAnchor(sectionKey, idx);
  if (guessed) {
    const exact = citationList.value.find((c) => c.anchor === guessed);
    if (exact) return exact;
    const partial = citationList.value.find((c) => typeof c.anchor === "string" && c.anchor.includes(guessed));
    if (partial) return partial;
  }

  const normalizedLine = String(lineText || "").trim();
  if (normalizedLine) {
    const quoteMatched = citationList.value.find((c) => String(c.text_quote || "").trim() === normalizedLine);
    if (quoteMatched) return quoteMatched;

    const included = citationList.value.find((c) => String(c.source_text || "").includes(normalizedLine));
    if (included) return included;
  }

  const sourceHint = sectionSourceHint[sectionKey];
  if (sourceHint) {
    const bySource = citationList.value.find((c) => c.source_type === sourceHint);
    if (bySource) return bySource;
  }

  return citationList.value[0] || null;
}

function openCitationFromSection(sectionKey, idx) {
  activeLink.value = `${sectionKey}-${idx}`;
  const linesBySection = {
    internal_requirements_3lines: internalRequirementLines.value,
    paper_tech_summary_3lines: paperTechLines.value,
    candidate_technologies_10lines: candidateTechLines.value,
    integration_design_10lines: integrationDesignLines.value,
    expected_impact_5lines: expectedImpactLines.value,
    limitations_and_risks_5lines: limitationRiskLines.value,
    final_conclusion_and_priorities_5lines: finalConclusionLines.value,
  };
  const currentLine = linesBySection[sectionKey]?.[idx] || "";
  const citation = findBestCitationForLine(sectionKey, idx, currentLine);
  openCitation(citation);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMarkdown(mdText) {
  if (!mdText) return "";
  const htmlParts = [];
  const lines = String(mdText).split("\n");
  let inList = false;

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      if (inList) {
        htmlParts.push("</ul>");
        inList = false;
      }
      continue;
    }

    if (line.startsWith("## ")) {
      if (inList) {
        htmlParts.push("</ul>");
        inList = false;
      }
      htmlParts.push(`<h3>${escapeHtml(line.slice(3))}</h3>`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!inList) {
        htmlParts.push("<ul>");
        inList = true;
      }
      htmlParts.push(`<li>${escapeHtml(line.slice(2))}</li>`);
      continue;
    }

    if (inList) {
      htmlParts.push("</ul>");
      inList = false;
    }
    htmlParts.push(`<p>${escapeHtml(line)}</p>`);
  }

  if (inList) htmlParts.push("</ul>");
  return htmlParts.join("");
}

const paperCitation = computed(() => {
  if (activeCitation.value?.source_type === "paper") return activeCitation.value;
  return citationList.value.find((c) => c.source_type === "paper") || null;
});

const internalCitation = computed(() => {
  if (activeCitation.value?.source_type === "internal") return activeCitation.value;
  return citationList.value.find((c) => c.source_type === "internal") || null;
});

const viewerCitation = computed(() => {
  if (activeTab.value === "사내문서") return internalCitation.value;
  return paperCitation.value;
});

const paperSummaryMarkdown = computed(() => {
  return paperSummaryMd.value || paperCitation.value?.source_text || reportSections.value.paper_tech_summary_3lines || DUMMY_PAPER_SUMMARY_MD;
});

const paperSummaryHtml = computed(() => renderMarkdown(paperSummaryMarkdown.value));

const paperOriginalUrl = computed(() => {
  if (paperCitation.value?.metadata?.paper_url) return String(paperCitation.value.metadata.paper_url);
  return DUMMY_PAPER_ORIGINAL_URL;
});

const internalPdfUrl = computed(() => {
  const base = (import.meta.env.VITE_INTERNAL_API || "/internal-api").replace(/\/$/, "");
  const metadata = internalCitation.value?.metadata || {};
  const sourceFile = metadata.source_file ? String(metadata.source_file) : "";

  if (sourceFile && sourceFile !== "unknown.pdf") {
    const fileName = sourceFile.split("/").pop() || sourceFile;
    return `${base}/assets/internal-docs/${encodeURIComponent(fileName)}`;
  }

  const docId = metadata.doc_id ? String(metadata.doc_id) : latestReport.value?.internal_doc_id;
  if (docId) return `${base}/assets/internal-docs/by-doc/${encodeURIComponent(docId)}`;
  return activeInternalDoc.value?.source_file
    ? `${base}/assets/internal-docs/${encodeURIComponent(activeInternalDoc.value.source_file)}`
    : `${base}/assets/internal-docs/`;
});

const hasPdfDoc = computed(() => {
  const metadata = internalCitation.value?.metadata || {};
  const sourceFile = String(metadata.source_file || '');
  if (sourceFile && sourceFile !== 'unknown.pdf') return true;
  const docFile = String(activeInternalDoc.value?.source_file || '');
  return !!(docFile && docFile !== 'unknown.pdf');
});

function readableCitationLabel(citation, idx) {
  const metaTitle = citation?.metadata?.title ? String(citation.metadata.title) : "";
  const anchor = citation?.anchor ? String(citation.anchor) : `ref-${idx + 1}`;
  if (citation?.source_type === "paper") {
    return `${metaTitle || "논문 근거"} (${anchor})`;
  }

  const pageNo = citation?.metadata?.page_no;
  const pagePart = Number.isInteger(pageNo) ? `, p.${pageNo}` : "";
  return `${metaTitle || "사내문서 근거"} (${anchor}${pagePart})`;
}

function readableSourceName(citation) {
  if (!citation) return "-";
  const metaTitle = citation?.metadata?.title ? String(citation.metadata.title) : "";
  if (metaTitle) return metaTitle;
  if (citation.source_type === "paper") return "논문 요약";
  return "사내문서";
}

const citationSegments = computed(() => {
  const c = viewerCitation.value;
  if (!c || !c.source_text) return { before: "", highlight: "", after: "" };

  const sourceText = String(c.source_text);
  let start = Number.isInteger(c.char_start) ? c.char_start : null;
  let end = Number.isInteger(c.char_end) ? c.char_end : null;

  if ((start === null || end === null) && c.text_quote) {
    const found = sourceText.indexOf(String(c.text_quote));
    if (found >= 0) {
      start = found;
      end = found + String(c.text_quote).length;
    }
  }

  if (start === null || end === null || start < 0 || end > sourceText.length || start >= end) {
    return { before: sourceText, highlight: "", after: "" };
  }

  return {
    before: sourceText.slice(0, start),
    highlight: sourceText.slice(start, end),
    after: sourceText.slice(end),
  };
});

async function runFixedCompare() {
  closeEventSource();
  reportLoading.value = true;
  reportError.value = "";
  resetSectionStatuses();
  try {
    // activeInternalDoc이 없으면 그 자리에서 다시 로드
    if (!activeInternalDoc.value) {
      const docs = await listInternalDocs();
      if (docs.length > 0) {
        activeInternalDoc.value = { doc_id: docs[0].doc_id, source_file: docs[0].source_file || "", title: docs[0].title || "" };
      }
    }
    if (!activeInternalDoc.value) throw new Error("사내문서가 없습니다. data/internal_docs 폴더에 PDF를 추가해주세요.");
    const accepted = await startReportGeneration({
      paper_id: FIXED_PAPER_ID,
      internal_doc_id: activeInternalDoc.value.doc_id,
    });
    latestReport.value = makeEmptyReport(accepted.report_id);
    activeCitation.value = null;
    activeLink.value = "";
    openSectionStream(accepted.report_id);
  } catch (error) {
    reportError.value = error?.response?.data?.detail || error?.message || "internal-service 목업 보고서 생성에 실패했습니다.";
    reportLoading.value = false;
  }
}

async function loadLatestReport() {
  try {
    const reports = await getReportList(1);
    if (reports.length > 0) {
      const data = await getReportById(reports[0].report_id);
      latestReport.value = data;
      completeAllSectionStatuses();
      return;
    }
  } catch {}
  await runFixedCompare();
}

function switchTab(tabId) {
  activeTab.value = tabId;
}

function drawBackground() {
  const canvas = bgCanvasEl.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const rect = rootEl.value?.getBoundingClientRect();
  const width = Math.max(1, Math.floor(rect?.width || window.innerWidth));
  const height = Math.max(1, Math.floor(rect?.height || window.innerHeight));

  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#03060e";
  ctx.fillRect(0, 0, width, height);

  const blueGlow = ctx.createRadialGradient(width * 0.15, height * 0.2, 0, width * 0.15, height * 0.2, width * 0.55);
  blueGlow.addColorStop(0, "rgba(18,50,170,0.28)");
  blueGlow.addColorStop(1, "rgba(3,6,14,0)");
  ctx.fillStyle = blueGlow;
  ctx.fillRect(0, 0, width, height);
}

onMounted(async () => {
  drawBackground();
  resizeHandler = () => drawBackground();
  window.addEventListener("resize", resizeHandler);

  if (store.pendingStreamReportId) {
    const reportId = store.pendingStreamReportId
    store.pendingStreamReportId = null
    resetSectionStatuses()
    reportLoading.value = true
    reportError.value = ''
    latestReport.value = makeEmptyReport(reportId)
    openSectionStream(reportId)
  } else if (store.currentReportId) {
    try {
      const data = await getReportById(store.currentReportId);
      latestReport.value = data;
      completeAllSectionStatuses();
    } catch {}
    store.currentReportId = null;
  } else {
    loadLatestReport();
  }

  // 사내문서 목록 로드 → 첫 번째 문서를 기본으로 사용
  try {
    const docs = await listInternalDocs();
    if (docs.length > 0) {
      activeInternalDoc.value = { doc_id: docs[0].doc_id, source_file: docs[0].source_file || "", title: docs[0].title || "" };
      const doc = await getInternalDocText(docs[0].doc_id);
      internalDocText.value = doc.text || "";
    }
  } catch {}
});

watch(
  () => latestReport.value?.paper_id,
  async (paperId) => {
    if (!paperId || paperId === FIXED_PAPER_ID) return;
    try {
      const paper = await fetchPaperById(paperId);
      const md = paper.md_summary || paper.summary_data?.summary || paper.abstract || "";
      if (md) paperSummaryMd.value = md;
    } catch {}
  }
);

onBeforeUnmount(() => {
  closeEventSource();
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
});
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Syne:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap");

.dashboard-root { font-family: "DM Sans", sans-serif; background: #f4f7fd; color: #080e1a; height: 100vh; overflow: hidden; position: relative; display: flex; flex-direction: column; }
.bg-canvas { display: none; }

.topbar { position: relative; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; background: #ffffff; border-bottom: 1px solid #ccd8ee; }
.logo { font-family: "Syne", sans-serif; font-size: 18px; font-weight: 700; letter-spacing: .05em; color: #080e1a; }
.logo span { color: #6688aa; }
.tabs { display: flex; gap: 4px; }
.tab { font-size: 15px; padding: 6px 20px; border: 0; background: transparent; color: #6688aa; cursor: pointer; font-family: inherit; }
.tab.active { color: #080e1a; font-weight: 600; }
.searchbox { display: flex; align-items: center; gap: 7px; background: #f0f5ff; border: 1px solid #ccd8ee; border-radius: 20px; padding: 6px 15px; font-size: 14px; color: #6688aa; }

.body { position: relative; z-index: 10; display: grid; grid-template-columns: 1fr 1fr; flex: 1; min-height: 0; height: 0; }
.compare-left { display: flex; flex-direction: column; border-right: 1px solid #ccd8ee; overflow: hidden; min-height: 0; background: #f4f7fd; }
.compare-left-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 22px; border-bottom: 1px solid #ccd8ee; background: #ffffff; }
.compare-label { font-family: "Syne", sans-serif; font-size: 15px; font-weight: 700; color: #1e3a5f; letter-spacing: .03em; }
.compare-actions { display: flex; gap: 8px; }
.compare-act-btn { font-size: 14px; padding: 6px 14px; border-radius: 20px; border: 1px solid #ccd8ee; background: #f4f7fd; color: #1e3a5f; cursor: pointer; font-family: inherit; transition: background .14s; }
.compare-act-btn:hover { background: #e6eef8; }
.compare-act-btn.sec { background: transparent; color: #6688aa; }
.compare-doc-area { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
.compare-doc-scroll { flex: 1; min-height: 0; overflow-y: auto; padding: 22px 24px; }
.compare-doc-scroll::-webkit-scrollbar { width: 4px; }
.compare-doc-scroll::-webkit-scrollbar-track { background: transparent; }
.compare-doc-scroll::-webkit-scrollbar-thumb { background: #ccd8ee; border-radius: 4px; }
.compare-doc-scroll::-webkit-scrollbar-thumb:hover { background: #aec0d8; }

.rpt-overview { background: #ffffff; border: 1px solid #ccd8ee; border-radius: 14px; padding: 20px 22px; margin-bottom: 20px; box-shadow: 0 1px 6px rgba(13,27,46,.06); }
.rpt-overview-title { font-family: "Syne", sans-serif; font-size: 17px; font-weight: 700; color: #080e1a; margin-bottom: 10px; }
.rpt-overview-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.rpt-meta-chip { font-size: 13px; padding: 3px 10px; border-radius: 10px; background: rgba(37,99,235,.1); color: #2563eb; font-weight: 500; }
.chip-internal { background: #f0f5ff; color: #6688aa; }
.rpt-meta-date { font-size: 13px; color: #6688aa; }
.rpt-summary { font-size: 15px; line-height: 1.75; color: #1e3a5f; }

.json-report-card { margin-top: 14px; border: 1px solid #ccd8ee; background: #ffffff; border-radius: 12px; padding: 12px; }
.json-report-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.json-report-title { font-size: 13px; font-weight: 700; letter-spacing: .06em; color: #1e3a5f; }
.json-report-status { font-size: 13px; color: #6688aa; }
.json-report-status.err { color: #dc2626; }
.json-report-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 6px; margin-bottom: 8px; }
.json-chip { font-size: 13px; color: #1e3a5f; background: #f4f7fd; border: 1px solid #ccd8ee; border-radius: 8px; padding: 5px 8px; }
.json-report-pre { margin: 0; max-height: 220px; overflow: auto; background: #f4f7fd; border-radius: 8px; border: 1px solid #ccd8ee; padding: 10px; font-size: 13px; line-height: 1.5; color: #1e3a5f; white-space: pre-wrap; }

.mapping-table-wrap { overflow-x: auto; border: 1px solid #ccd8ee; border-radius: 12px; background: #ffffff; }
.mapping-table { width: 100%; min-width: 920px; border-collapse: collapse; table-layout: fixed; }
.mapping-table col.col-requirement { width: 220px; }
.mapping-table col.col-tech-id { width: 130px; }
.mapping-table col.col-score { width: 88px; }
.mapping-table th,
.mapping-table td { border-bottom: 1px solid #e6eef8; border-right: 1px solid #e6eef8; padding: 10px 12px; vertical-align: top; text-align: left; word-break: break-word; }
.mapping-table th:last-child,
.mapping-table td:last-child { border-right: none; }
.mapping-table thead th { position: sticky; top: 0; background: #f4f7fd; color: #1e3a5f; font-size: 13px; font-weight: 700; letter-spacing: .03em; z-index: 1; }
.mapping-table tbody td { font-size: 14px; line-height: 1.65; color: #1e3a5f; }
.mapping-table th:nth-child(5),
.mapping-table td:nth-child(5) { text-align: center; white-space: nowrap; }
.mapping-table tbody tr:last-child td { border-bottom: none; }

.rpt-section { display: flex; gap: 16px; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #e6eef8; }
.rpt-last { border-bottom: none; margin-bottom: 8px; }
.rpt-sec-num { font-family: "Syne", sans-serif; font-size: 26px; font-weight: 700; color: rgba(37,99,235,.18); width: 32px; flex-shrink: 0; }
.rpt-sec-content { flex: 1; min-width: 0; }
.rpt-sec-title { font-family: "Syne", sans-serif; font-size: 14px; font-weight: 700; color: #1e3a5f; margin-bottom: 10px; letter-spacing: .03em; text-transform: uppercase; }
.sec-state { display: inline-flex; margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: 12px; letter-spacing: .03em; background: #f0f5ff; color: #6688aa; }
.sec-state.run { background: #fff7ed; color: #c2410c; }
.sec-state.done { background: rgba(0,212,170,.1); color: #059669; }
.rpt-bullets { display: flex; flex-direction: column; gap: 7px; }
.rpt-bullets.section-glass-loading { min-height: 74px; }
.rpt-bullet { display: flex; align-items: flex-start; gap: 10px; font-size: 15px; line-height: 1.72; color: #1e3a5f; }
.section-glass-loading {
  position: relative; border-radius: 10px; overflow: hidden; padding: 8px 0;
  --skel-w1: 100%; --skel-w2: 72%; --skel-h: 18px; --skel-gap: 11px; --skel-delay: .35s;
}
.mapping-table-wrap.section-glass-loading,
.json-report-pre.section-glass-loading { min-height: 94px; }
.section-glass-loading::before,
.section-glass-loading::after {
  content: ""; display: block; height: var(--skel-h); border-radius: 999px;
  background: linear-gradient(90deg, #e6eef8, #f4f7fd, #e6eef8);
  animation: skeletonPulse 2.6s ease-in-out infinite; pointer-events: none;
}
.section-glass-loading::before { width: var(--skel-w1); }
.section-glass-loading::after { width: var(--skel-w2); margin-top: var(--skel-gap); animation-delay: var(--skel-delay); }
.rpt-section:nth-of-type(1) .section-glass-loading { --skel-w1: 96%; --skel-w2: 68%; }
.rpt-section:nth-of-type(2) .section-glass-loading { --skel-w1: 88%; --skel-w2: 74%; }
.rpt-section:nth-of-type(3) .section-glass-loading { --skel-w1: 100%; --skel-w2: 60%; --skel-h: 20px; }
.rpt-section:nth-of-type(4) .section-glass-loading { --skel-w1: 91%; --skel-w2: 80%; }
.rpt-section:nth-of-type(5) .section-glass-loading { --skel-w1: 84%; --skel-w2: 65%; }
.rpt-section:nth-of-type(6) .section-glass-loading { --skel-w1: 94%; --skel-w2: 56%; }
.rpt-section:nth-of-type(7) .section-glass-loading { --skel-w1: 90%; --skel-w2: 73%; }
@keyframes skeletonPulse { 0% { opacity: .9; } 50% { opacity: .3; } 100% { opacity: .9; } }

.bul-dot { width: 6px; height: 6px; border-radius: 50%; background: #aec0d8; margin-top: 6px; flex-shrink: 0; }
.bul-blue { background: #2563eb; }
.bul-orange { background: #f97316; }
.bul-red { background: #ef4444; }
.bul-idx { font-family: "Syne", sans-serif; font-size: 13px; font-weight: 700; color: rgba(37,99,235,.5); width: 16px; margin-top: 2px; flex-shrink: 0; }
.linkable { cursor: pointer; transition: background .18s; border-radius: 8px; padding: 5px 8px; margin: -5px -8px; }
.linkable:hover { background: rgba(37,99,235,.07); }
.linkable.active-link { background: rgba(37,99,235,.11); }
.link-arrow { font-size: 12px; color: rgba(37,99,235,.5); margin-left: 6px; opacity: 0; transition: opacity .15s; }
.linkable:hover .link-arrow { opacity: 1; }

.compare-right { display: flex; flex-direction: column; overflow: hidden; background: #ffffff; min-height: 0; }
.doc-tabs { display: flex; gap: 0; padding: 12px 22px 0; border-bottom: 1px solid #ccd8ee; background: #ffffff; }
.doc-tab { font-size: 14px; padding: 8px 18px; border-radius: 12px 12px 0 0; border: 1px solid transparent; border-bottom: 0; background: transparent; color: #6688aa; cursor: pointer; margin-right: 2px; font-family: inherit; transition: color .14s; }
.doc-tab.active { background: #f4f7fd; color: #080e1a; font-weight: 600; border-color: #ccd8ee; border-bottom: 0; }
.doc-viewer { flex: 1; overflow: hidden; display: flex; flex-direction: column; min-height: 0; background: #f4f7fd; }
.doc-content { flex: 1; min-height: 0; overflow-y: auto; padding: 24px 26px; }
.doc-content::-webkit-scrollbar { width: 4px; }
.doc-content::-webkit-scrollbar-track { background: transparent; }
.doc-content::-webkit-scrollbar-thumb { background: #ccd8ee; border-radius: 4px; }
.doc-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.doc-meta-tag { font-size: 13px; padding: 3px 10px; border-radius: 10px; background: #f0f5ff; color: #2563eb; font-weight: 500; }
.doc-meta-date, .doc-meta-author { font-size: 13px; color: #6688aa; }
.doc-title-big { font-family: "Syne", sans-serif; font-size: 19px; font-weight: 700; color: #080e1a; margin-bottom: 6px; }
.doc-subtitle { font-size: 14px; color: #6688aa; margin-bottom: 20px; }
.doc-body-text { font-size: 15px; line-height: 1.8; color: #1e3a5f; display: flex; flex-direction: column; gap: 14px; }
.doc-highlight-box { background: #f0f5ff; border-radius: 14px; padding: 16px 18px; border: 1px solid #ccd8ee; }
.doc-hl-title { font-size: 12px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: #2563eb; margin-bottom: 10px; }
.citation-mark { background: rgba(37,99,235,.15); color: #080e1a; padding: 0 2px; border-radius: 2px; }
.doc-embed-wrap { border-radius: 12px; overflow: hidden; border: 1px solid #ccd8ee; background: #ffffff; min-height: 520px; }
.doc-embed-frame { width: 100%; height: 520px; border: 0; background: #ffffff; }
.internal-doc-text { white-space: pre-wrap; font-size: 15px; line-height: 1.8; color: #1e3a5f; background: #ffffff; border: 1px solid #ccd8ee; border-radius: 12px; padding: 18px 22px; overflow-y: auto; max-height: 520px; }
.md-render h3 { font-family: "Syne", sans-serif; font-size: 15px; color: #080e1a; margin: 10px 0 6px; font-weight: 700; }
.md-render p { margin: 0 0 8px; color: #1e3a5f; }
.md-render ul { margin: 0 0 10px 18px; }
.md-render li { margin: 0 0 6px; color: #1e3a5f; }

.paper-open-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 10px;
  background: rgba(37,99,235,.1); color: #2563eb;
  border: 1px solid rgba(37,99,235,.25); font-size: 14px;
  font-weight: 600; cursor: pointer; text-decoration: none;
  transition: background .15s; margin-bottom: 8px;
}
.paper-open-btn:hover { background: rgba(37,99,235,.2); }
.paper-iframe-notice { font-size: 12px; color: #6688aa; margin-bottom: 12px; }

@media (max-width: 1024px) {
  .body { grid-template-columns: 1fr; }
  .compare-left { border-right: none; border-bottom: 1px solid #ccd8ee; min-height: 45vh; }
  .topbar { gap: 16px; flex-wrap: wrap; }
  .tabs { order: 3; width: 100%; overflow-x: auto; }
}
</style>
