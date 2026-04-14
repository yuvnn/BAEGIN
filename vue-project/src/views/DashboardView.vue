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
              {{ reportLoading ? "순차 실행 중..." : "고정 ID 비교 실행" }}
            </button>
            <button class="compare-act-btn sec" type="button" @click="loadLatestReport">최신 JSON 불러오기</button>
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

              <div class="json-report-card">
                <div class="json-report-head">
                  <div class="json-report-title">저장된 최신 비교 JSON</div>
                  <div v-if="reportLoading" class="json-report-status">로딩 중...</div>
                  <div v-else-if="reportError" class="json-report-status err">{{ reportError }}</div>
                  <div v-else-if="latestReport?.saved_at" class="json-report-status">{{ latestReport.saved_at }}</div>
                </div>

                <template v-if="latestReport">
                  <div class="json-report-grid">
                    <div class="json-chip">paper_id: {{ latestReport.paper_id || "-" }}</div>
                    <div class="json-chip">query: {{ latestReport.query_text || "-" }}</div>
                    <div class="json-chip">paper_hits: {{ paperHitCount }}</div>
                    <div class="json-chip">internal_hits: {{ internalHitCount }}</div>
                  </div>
                  <pre class="json-report-pre">{{ latestReportPretty }}</pre>
                </template>
              </div>
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
              <span class="doc-meta-date">anchor: {{ activeCitation?.anchor || '-' }}</span>
              <span class="doc-meta-author">source_type: {{ activeCitation?.source_type || '-' }}</span>
            </div>

            <div class="doc-title-big">Citation Source Viewer</div>
            <div class="doc-subtitle">anchor 기준 citation 매핑 · source_text 하이라이트</div>

            <div class="doc-body-text">
              <template v-if="activeCitation">
                <p><strong>source_id:</strong> {{ activeCitation.source_id || '-' }}</p>
                <div class="doc-highlight-box">
                  <div class="doc-hl-title">source_text (char highlight)</div>
                  <p class="doc-raw">
                    <span>{{ citationSegments.before }}</span>
                    <mark class="citation-mark">{{ citationSegments.highlight || '하이라이트 가능한 범위 없음' }}</mark>
                    <span>{{ citationSegments.after }}</span>
                  </p>
                </div>
                <p>범위: {{ activeCitation.char_start ?? '-' }} ~ {{ activeCitation.char_end ?? '-' }}</p>
              </template>
              <template v-else>
                <p>선택된 citation이 없습니다. 좌측 문장을 클릭해 주세요.</p>
              </template>

              <div class="rpt-overview" style="padding:12px;margin-top:8px;">
                <div class="rpt-sec-title">citation 목록</div>
                <div class="rpt-bullets">
                  <div
                    v-for="(c, idx) in citationList"
                    :key="`citation-${c.citation_id}-${idx}`"
                    class="rpt-bullet linkable"
                    @click="openCitation(c)"
                  >
                    <span class="bul-dot" :class="c.source_type === 'paper' ? 'bul-blue' : ''"></span>
                    [{{ c.source_type }}] {{ c.anchor || 'no-anchor' }} / {{ c.source_id }}
                  </div>
                  <div v-if="citationList.length === 0" class="rpt-bullet">citation 데이터 없음</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { getReportStreamUrl, startReportGeneration } from "../api/reportService";

const rootEl = ref(null);
const bgCanvasEl = ref(null);
const activeTab = ref("사내문서");
const activeLink = ref("");
const latestReport = ref(null);
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
const FIXED_INTERNAL_DOC_ID = "internal-b482da9a0b960bde";
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
const citationList = computed(() => latestReport.value?.citations || []);

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
    internal_doc_id: FIXED_INTERNAL_DOC_ID,
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

const paperHitCount = computed(() => latestReport.value?.comparison?.paper_hits?.ids?.[0]?.length || 0);
const internalHitCount = computed(() => latestReport.value?.comparison?.internal_hits?.ids?.[0]?.length || 0);
const latestReportPretty = computed(() => (latestReport.value ? JSON.stringify(latestReport.value, null, 2) : ""));

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

function openCitationFromSection(sectionKey, idx) {
  activeLink.value = `${sectionKey}-${idx}`;
  const guessed = resolveAnchor(sectionKey, idx);
  let citation = null;

  if (guessed) citation = citationList.value.find((c) => c.anchor === guessed);
  if (!citation && guessed) citation = citationList.value.find((c) => typeof c.anchor === "string" && c.anchor.includes(guessed));

  if (!citation) {
    const sourceHint = sectionSourceHint[sectionKey];
    if (sourceHint) citation = citationList.value.find((c) => c.source_type === sourceHint);
  }

  if (!citation && citationList.value.length > 0) citation = citationList.value[0];
  openCitation(citation);
}

const citationSegments = computed(() => {
  const c = activeCitation.value;
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
    const accepted = await startReportGeneration({
      paper_id: FIXED_PAPER_ID,
      internal_doc_id: FIXED_INTERNAL_DOC_ID,
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

async function loadLatestReport(raiseOnFail = false) {
  try {
    await runFixedCompare();
  } catch (error) {
    if (raiseOnFail) throw error;
  }
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

onMounted(() => {
  drawBackground();
  resizeHandler = () => drawBackground();
  window.addEventListener("resize", resizeHandler);
  loadLatestReport();
});

onBeforeUnmount(() => {
  closeEventSource();
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
});
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Syne:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap");

html,
body,
#app { height: 100%; margin: 0; background: #03060e; overflow: hidden; }
* { box-sizing: border-box; margin: 0; padding: 0; }

.dashboard-root { font-family: "DM Sans", sans-serif; background: #03060e; color: rgba(210,220,245,.92); height: 100vh; overflow: hidden; position: relative; display: flex; flex-direction: column; }
.bg-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }

.topbar { position: relative; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 14px 24px; background: rgba(2,6,15,.55); backdrop-filter: blur(40px) saturate(180%); box-shadow: 0 1px 0 rgba(37,99,235,.07); }
.logo { font-family: "Syne", sans-serif; font-size: 15px; font-weight: 700; letter-spacing: .05em; color: #fff; }
.logo span { color: rgba(255,255,255,.6); }
.tabs { display: flex; gap: 4px; }
.tab { font-size: 12px; padding: 6px 20px; border: 0; background: transparent; color: rgba(140,160,220,.45); cursor: pointer; }
.tab.active { color: #dde5ff; font-weight: 500; }
.searchbox { display: flex; align-items: center; gap: 7px; background: rgba(255,255,255,.05); border-radius: 20px; padding: 6px 15px; font-size: 11px; color: rgba(148,164,208,.6); }

.body { position: relative; z-index: 10; display: grid; grid-template-columns: 1fr 1fr; flex: 1; min-height: 0; }
.compare-left { display: flex; flex-direction: column; border-right: .5px solid rgba(255,255,255,.06); overflow: hidden; }
.compare-left-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 22px; border-bottom: .5px solid rgba(255,255,255,.06); }
.compare-label { font-family: "Syne", sans-serif; font-size: 12px; font-weight: 700; color: rgba(220,230,255,.7); }
.compare-actions { display: flex; gap: 8px; }
.compare-act-btn { font-size: 11px; padding: 6px 14px; border-radius: 20px; border: 0; background: rgba(37,99,235,.2); color: rgba(180,205,255,.85); cursor: pointer; }
.compare-act-btn.sec { background: rgba(255,255,255,.06); color: rgba(160,180,230,.65); }
.compare-doc-area { flex: 1; overflow: hidden; }
.compare-doc-scroll { height: 100%; overflow-y: auto; padding: 22px 24px; }

.rpt-overview { background: rgba(37,99,235,.1); border-radius: 16px; padding: 20px 22px; margin-bottom: 24px; }
.rpt-overview-title { font-family: "Syne", sans-serif; font-size: 14px; font-weight: 700; color: rgba(220,232,255,.92); margin-bottom: 10px; }
.rpt-overview-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.rpt-meta-chip { font-size: 9.5px; padding: 3px 10px; border-radius: 10px; background: rgba(37,99,235,.2); color: rgba(147,197,253,.85); }
.chip-internal { background: rgba(255,255,255,.08); color: rgba(200,215,255,.7); }
.rpt-meta-date { font-size: 9.5px; color: rgba(120,145,200,.45); }
.rpt-summary { font-size: 11.5px; line-height: 1.75; color: rgba(185,205,245,.75); }

.json-report-card { margin-top: 14px; border: 1px solid rgba(37,99,235,.25); background: rgba(4,12,30,.6); border-radius: 12px; padding: 12px; }
.json-report-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.json-report-title { font-size: 10px; font-weight: 700; letter-spacing: .06em; color: rgba(160,200,255,.85); }
.json-report-status { font-size: 10px; color: rgba(165,185,230,.7); }
.json-report-status.err { color: rgba(252,165,165,.9); }
.json-report-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 6px; margin-bottom: 8px; }
.json-chip { font-size: 10px; color: rgba(205,220,255,.84); background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 8px; padding: 5px 8px; }
.json-report-pre { margin: 0; max-height: 220px; overflow: auto; background: rgba(0,0,0,.25); border-radius: 8px; border: 1px solid rgba(255,255,255,.08); padding: 10px; font-size: 10px; line-height: 1.5; color: rgba(185,205,245,.82); white-space: pre-wrap; }

.mapping-table-wrap { overflow-x: auto; border: 1px solid rgba(255,255,255,.1); border-radius: 12px; background: rgba(2,10,28,.55); }
.mapping-table { width: 100%; min-width: 920px; border-collapse: collapse; table-layout: fixed; }
.mapping-table col.col-requirement { width: 220px; }
.mapping-table col.col-tech-id { width: 130px; }
.mapping-table col.col-score { width: 88px; }
.mapping-table th,
.mapping-table td { border-bottom: 1px solid rgba(255,255,255,.08); border-right: 1px solid rgba(255,255,255,.06); padding: 10px 12px; vertical-align: top; text-align: left; word-break: break-word; }
.mapping-table th:last-child,
.mapping-table td:last-child { border-right: none; }
.mapping-table thead th { position: sticky; top: 0; background: rgba(10,26,58,.96); color: rgba(196,218,255,.95); font-size: 10px; font-weight: 700; letter-spacing: .03em; z-index: 1; }
.mapping-table tbody td { font-size: 10.5px; line-height: 1.65; color: rgba(185,205,245,.86); }
.mapping-table th:nth-child(5),
.mapping-table td:nth-child(5) { text-align: center; white-space: nowrap; }
.mapping-table tbody tr:last-child td { border-bottom: none; }

.rpt-section { display: flex; gap: 16px; margin-bottom: 22px; padding-bottom: 22px; border-bottom: .5px solid rgba(255,255,255,.06); }
.rpt-last { border-bottom: none; margin-bottom: 8px; }
.rpt-sec-num { font-family: "Syne", sans-serif; font-size: 22px; font-weight: 700; color: rgba(37,99,235,.22); width: 32px; }
.rpt-sec-content { flex: 1; min-width: 0; }
.rpt-sec-title { font-family: "Syne", sans-serif; font-size: 11px; font-weight: 700; color: rgba(200,218,255,.75); margin-bottom: 10px; }
.sec-state { display: inline-flex; margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: 9px; letter-spacing: .03em; background: rgba(255,255,255,.08); color: rgba(205,220,255,.8); }
.sec-state.run { background: rgba(255,255,255,.12); color: rgba(235,242,255,.85); }
.sec-state.done { background: rgba(56,189,248,.18); color: rgba(186,230,253,.95); }
.rpt-bullets { display: flex; flex-direction: column; gap: 7px; }
.rpt-bullets.section-glass-loading { min-height: 74px; }
.rpt-bullet { display: flex; align-items: flex-start; gap: 10px; font-size: 11px; line-height: 1.72; color: rgba(175,195,240,.72); }
.section-glass-loading {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  padding: 8px 0;
  --skel-w1: 100%;
  --skel-w2: 72%;
  --skel-h: 18px;
  --skel-gap: 11px;
  --skel-delay: .35s;
}
.mapping-table-wrap.section-glass-loading,
.json-report-pre.section-glass-loading { min-height: 94px; }
.section-glass-loading::before,
.section-glass-loading::after {
  content: "";
  display: block;
  height: var(--skel-h);
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(255,255,255,.11), rgba(255,255,255,.05), rgba(255,255,255,.11));
  animation: skeletonPulse 2.6s ease-in-out infinite;
  pointer-events: none;
}

.section-glass-loading::before { width: var(--skel-w1); }
.section-glass-loading::after {
  width: var(--skel-w2);
  margin-top: var(--skel-gap);
  animation-delay: var(--skel-delay);
}

.rpt-section:nth-of-type(1) .section-glass-loading {
  --skel-w1: 96%;
  --skel-w2: 68%;
}

.rpt-section:nth-of-type(2) .section-glass-loading {
  --skel-w1: 88%;
  --skel-w2: 74%;
}

.rpt-section:nth-of-type(3) .section-glass-loading {
  --skel-w1: 100%;
  --skel-w2: 60%;
  --skel-h: 20px;
}

.rpt-section:nth-of-type(4) .section-glass-loading {
  --skel-w1: 91%;
  --skel-w2: 80%;
}

.rpt-section:nth-of-type(5) .section-glass-loading {
  --skel-w1: 84%;
  --skel-w2: 65%;
}

.rpt-section:nth-of-type(6) .section-glass-loading {
  --skel-w1: 94%;
  --skel-w2: 56%;
}

.rpt-section:nth-of-type(7) .section-glass-loading {
  --skel-w1: 90%;
  --skel-w2: 73%;
}

@keyframes skeletonPulse {
  0% { opacity: .78; }
  50% { opacity: .22; }
  100% { opacity: .78; }
}
.bul-dot { width: 6px; height: 6px; border-radius: 50%; background: rgba(255,255,255,.2); margin-top: 6px; }
.bul-blue { background: rgba(37,99,235,.7); }
.bul-orange { background: rgba(255,122,47,.75); }
.bul-red { background: rgba(239,68,68,.7); }
.bul-idx { font-family: "Syne", sans-serif; font-size: 10px; font-weight: 700; color: rgba(37,99,235,.5); width: 16px; margin-top: 2px; }
.linkable { cursor: pointer; transition: background .18s; border-radius: 8px; padding: 5px 8px; margin: -5px -8px; }
.linkable:hover { background: rgba(37,99,235,.1); }
.linkable.active-link { background: rgba(37,99,235,.16); }
.link-arrow { font-size: 9px; color: rgba(37,99,235,.5); margin-left: 6px; opacity: 0; transition: opacity .15s; }
.linkable:hover .link-arrow { opacity: 1; }

.compare-right { display: flex; flex-direction: column; overflow: hidden; background: rgba(255,255,255,.02); }
.doc-tabs { display: flex; gap: 0; padding: 12px 22px 0; border-bottom: .5px solid rgba(255,255,255,.07); }
.doc-tab { font-size: 11px; padding: 8px 18px; border-radius: 12px 12px 0 0; border: 0; background: transparent; color: rgba(140,160,210,.45); cursor: pointer; margin-right: 2px; }
.doc-tab.active { background: rgba(255,255,255,.07); color: rgba(215,228,255,.9); }
.doc-viewer { flex: 1; overflow: hidden; }
.doc-content { height: 100%; overflow-y: auto; padding: 24px 26px; }
.doc-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.doc-meta-tag { font-size: 9.5px; padding: 3px 10px; border-radius: 10px; background: rgba(255,255,255,.09); color: rgba(190,210,255,.8); }
.doc-meta-date, .doc-meta-author { font-size: 9.5px; color: rgba(130,150,200,.45); }
.doc-title-big { font-family: "Syne", sans-serif; font-size: 16px; font-weight: 700; color: rgba(225,235,255,.92); margin-bottom: 6px; }
.doc-subtitle { font-size: 10.5px; color: rgba(130,150,205,.5); margin-bottom: 20px; }
.doc-body-text { font-size: 11.5px; line-height: 1.8; color: rgba(185,200,240,.72); display: flex; flex-direction: column; gap: 14px; }
.doc-raw { font-size: 11px; line-height: 1.85; }
.doc-highlight-box { background: rgba(255,255,255,.05); border-radius: 14px; padding: 16px 18px; border-left: 2px solid rgba(37,99,235,.4); }
.doc-hl-title { font-size: 9px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: rgba(37,99,235,.65); margin-bottom: 10px; }
.citation-mark { background: rgba(37,99,235,.35); color: rgba(230,240,255,.95); padding: 0 2px; }

@media (max-width: 1024px) {
  .body { grid-template-columns: 1fr; }
  .compare-left { border-right: none; border-bottom: .5px solid rgba(255,255,255,.06); min-height: 45vh; }
  .topbar { gap: 16px; flex-wrap: wrap; }
  .tabs { order: 3; width: 100%; overflow-x: auto; }
}
</style>
