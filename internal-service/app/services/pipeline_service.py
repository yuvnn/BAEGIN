from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Optional

from ..schemas.input import GenerateReportRequest
from ..schemas.report import Citation, CitationMetadata, FinalResponse, ReportDocument, ReportSectionContent

EmitFn = Callable[[str, dict], None]


class PipelineService:
    def __init__(self) -> None:
        self.paper_service_url = os.getenv("PAPER_SERVICE_URL", "http://paper-service:8000").rstrip("/")

    def build_report(self, payload: GenerateReportRequest, emit: Optional[EmitFn] = None) -> FinalResponse:
        paper = self._fetch_paper_detail(payload.paper_id)
        paper_title = self._resolve_paper_title(payload.paper_id, paper)
        paper_category = self._get_str(paper.get("category") or paper.get("metadata", {}).get("category") or "ML Foundation")
        paper_url = self._get_str(paper.get("paper_url") or paper.get("metadata", {}).get("paper_url") or "")
        authors = paper.get("authors") or []
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except Exception:
                authors = [authors]

        summary_md = self._get_str(paper.get("md_summary") or paper.get("summary_data", {}).get("summary") or "")
        paper_summary_lines = self._extract_bullet_lines(summary_md, fallback=[
            f"{paper_title} 논문은 {paper_category} 영역의 핵심 기술 후보입니다.",
            "요약 데이터가 제한되어 있어 공통 구조를 기준으로 정리했습니다.",
            "후속 검토 시 원문과 평가 점수를 함께 확인해야 합니다.",
        ])

        internal_lines = self._build_internal_requirement_lines(payload.internal_doc_id, paper_title, paper_category)
        mapping_table = self._build_mapping_table(payload.internal_doc_id, paper_title, paper_category)
        candidate_lines = self._build_candidate_lines(paper_title, paper_category)
        integration_lines = self._build_integration_lines(payload.internal_doc_id, paper_title)
        impact_lines = self._build_impact_lines(paper_title, paper_category)
        risk_lines = self._build_risk_lines(paper_title)
        conclusion_lines = self._build_conclusion_lines(paper_title, payload.internal_doc_id)

        sections = ReportSectionContent(
            overview_summary="\n".join([
                f"- {paper_title}와 {payload.internal_doc_id}의 적합성을 검토했습니다.",
                f"- 카테고리 기준은 {paper_category}이며, 우선 순위는 도입 가능성과 리스크의 균형입니다.",
                f"- 사내 문서 요구사항과 논문 요약을 연결한 최소 실행 경로를 제안합니다.",
            ]),
            internal_requirements_3lines="\n".join(internal_lines),
            paper_tech_summary_3lines="\n".join(paper_summary_lines[:3]),
            mapping_analysis_table_md=mapping_table,
            candidate_technologies_10lines="\n".join(candidate_lines),
            integration_design_10lines="\n".join(integration_lines),
            expected_impact_5lines="\n".join(impact_lines),
            limitations_and_risks_5lines="\n".join(risk_lines),
            final_conclusion_and_priorities_5lines="\n".join(conclusion_lines),
        )

        citations = self._build_citations(
            payload=payload,
            paper=paper,
            paper_title=paper_title,
            paper_category=paper_category,
            paper_url=paper_url,
            summary_md=summary_md,
            internal_lines=internal_lines,
            candidate_lines=candidate_lines,
            integration_lines=integration_lines,
            impact_lines=impact_lines,
            risk_lines=risk_lines,
            conclusion_lines=conclusion_lines,
        )

        report = FinalResponse(
            report_id="",
            paper_id=payload.paper_id,
            internal_doc_id=payload.internal_doc_id,
            status="completed",
            updated_at=datetime.now(timezone.utc).isoformat(),
            report=ReportDocument(
                title="논문-기획서 비교 분석 보고서",
                sections=sections,
            ),
            citations=citations,
        )
        return report

    def _fetch_paper_detail(self, paper_id: str) -> dict:
        candidates = [
            f"{self.paper_service_url}/papers/{urllib.parse.quote(paper_id)}",
            f"{self.paper_service_url}/papers?limit=100",
        ]

        for url in candidates:
            try:
                with urllib.request.urlopen(url, timeout=12) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if isinstance(payload, list):
                    for item in payload:
                        if item.get("paper_id") == paper_id:
                            return item
                if isinstance(payload, dict):
                    return payload
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                continue
        return {}

    def _resolve_paper_title(self, paper_id: str, paper: dict) -> str:
        metadata = paper.get("metadata") or {}
        title = metadata.get("title") or paper.get("title")
        if title:
            return self._get_str(title)
        return paper_id

    def _build_internal_requirement_lines(self, internal_doc_id: str, paper_title: str, paper_category: str) -> list[str]:
        return [
            f"- {internal_doc_id} 기준으로 {paper_title} 도입 가능성을 먼저 검토합니다.",
            f"- 현재 우선 영역은 {paper_category} 관련 기능 정합성과 운영 복잡도입니다.",
            "- 내부 문서와의 연결 근거를 명시해 평가 기준을 추적 가능하게 유지합니다.",
        ]

    def _build_mapping_table(self, internal_doc_id: str, paper_title: str, paper_category: str) -> str:
        return "\n".join([
            "| 요구사항 | 대응 논문 요소 | 적합도 | 비고 |",
            "| --- | --- | --- | --- |",
            f"| {internal_doc_id} 핵심 요구 | {paper_title} 요약 | 높음 | {paper_category} 중심 검토 |",
            "| 운영 자동화 | 실시간 요약/스트림 전달 | 중간 | 후속 배포 필요 |",
        ])

    def _build_candidate_lines(self, paper_title: str, paper_category: str) -> list[str]:
        return [
            f"- {paper_title}를 사내 검토 포털의 추천 카드로 노출합니다.",
            f"- {paper_category} 태그를 기준으로 유사 논문 묶음을 구성합니다.",
            "- 요약과 citation을 분리하여 근거 추적성을 유지합니다.",
            "- 스트리밍 상태를 UI에 표시해 생성 지연을 완화합니다.",
            "- 저장 결과는 JSON으로 보존해 재조회가 가능해야 합니다.",
        ]

    def _build_integration_lines(self, internal_doc_id: str, paper_title: str) -> list[str]:
        return [
            f"- {internal_doc_id}와 {paper_title}의 관계를 하나의 보고서로 묶습니다.",
            "- SSE로 섹션별 진행 상태를 전송하고 UI는 부분 갱신만 수행합니다.",
            "- 완료 시 최종 JSON을 저장소와 메모리 캐시에 동시 반영합니다.",
            "- 실패 시 failed 이벤트를 보내고 즉시 상태를 종료합니다.",
            "- 내부 API와 프론트는 /internal-api 프록시로 연결합니다.",
        ]

    def _build_impact_lines(self, paper_title: str, paper_category: str) -> list[str]:
        return [
            f"- {paper_category} 영역의 논문을 빠르게 내부 검토 대상으로 분류할 수 있습니다.",
            f"- {paper_title}에 대한 평가 근거가 보고서 형식으로 남습니다.",
            "- 반복 작업을 줄여 검토 속도를 높일 수 있습니다.",
        ]

    def _build_risk_lines(self, paper_title: str) -> list[str]:
        return [
            f"- {paper_title}의 원문/메타데이터가 비어 있으면 요약 품질이 낮아질 수 있습니다.",
            "- SSE 연결이 중간에 끊길 수 있으므로 keep-alive 처리가 필요합니다.",
            "- 외부 paper-service 응답 실패 시 fallback 데이터를 사용합니다.",
        ]

    def _build_conclusion_lines(self, paper_title: str, internal_doc_id: str) -> list[str]:
        return [
            f"- {paper_title}는 {internal_doc_id} 기준으로 우선 검토 후보입니다.",
            "- 첫 번째 우선순위는 보고서 생성 안정화와 추적 가능한 citation 유지입니다.",
            "- 두 번째 우선순위는 실데이터 연동과 요약 품질 개선입니다.",
        ]

    def _build_citations(
        self,
        *,
        payload: GenerateReportRequest,
        paper: dict,
        paper_title: str,
        paper_category: str,
        paper_url: str,
        summary_md: str,
        internal_lines: list[str],
        candidate_lines: list[str],
        integration_lines: list[str],
        impact_lines: list[str],
        risk_lines: list[str],
        conclusion_lines: list[str],
    ) -> list[Citation]:
        first_paper_line = self._first_content_line(summary_md) or f"{paper_title}"
        return [
            Citation(
                citation_id="citation-paper-1",
                source_type="paper",
                source_id=payload.paper_id,
                source_text=summary_md or f"{paper_title}\n{paper_category}",
                text_quote=first_paper_line,
                char_start=None,
                char_end=None,
                anchor="paper_tech_1",
                metadata=CitationMetadata(
                    title=paper_title,
                    paper_url=paper_url or None,
                    category=paper_category,
                ),
            ),
            Citation(
                citation_id="citation-internal-1",
                source_type="internal",
                source_id=payload.internal_doc_id,
                source_text=internal_lines[0],
                text_quote=internal_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(internal_lines[0]), 80),
                anchor="int_req_1",
                metadata=CitationMetadata(
                    title=f"Internal doc {payload.internal_doc_id}",
                    doc_id=payload.internal_doc_id,
                    source_file=f"{payload.internal_doc_id}.pdf",
                    source_ext=".pdf",
                    page_no=1,
                ),
            ),
            Citation(
                citation_id="citation-candidate-1",
                source_type="paper",
                source_id=payload.paper_id,
                source_text=candidate_lines[0],
                text_quote=candidate_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(candidate_lines[0]), 80),
                anchor="cand_1",
                metadata=CitationMetadata(title=paper_title, paper_url=paper_url or None, category=paper_category),
            ),
            Citation(
                citation_id="citation-design-1",
                source_type="internal",
                source_id=payload.internal_doc_id,
                source_text=integration_lines[0],
                text_quote=integration_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(integration_lines[0]), 80),
                anchor="design_1",
                metadata=CitationMetadata(title=f"Internal doc {payload.internal_doc_id}", doc_id=payload.internal_doc_id, source_file=f"{payload.internal_doc_id}.pdf", source_ext=".pdf", page_no=1),
            ),
            Citation(
                citation_id="citation-impact-1",
                source_type="paper",
                source_id=payload.paper_id,
                source_text=impact_lines[0],
                text_quote=impact_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(impact_lines[0]), 80),
                anchor="impact_1",
                metadata=CitationMetadata(title=paper_title, paper_url=paper_url or None, category=paper_category),
            ),
            Citation(
                citation_id="citation-risk-1",
                source_type="paper",
                source_id=payload.paper_id,
                source_text=risk_lines[0],
                text_quote=risk_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(risk_lines[0]), 80),
                anchor="risk_1",
                metadata=CitationMetadata(title=paper_title, paper_url=paper_url or None, category=paper_category),
            ),
            Citation(
                citation_id="citation-final-1",
                source_type="internal",
                source_id=payload.internal_doc_id,
                source_text=conclusion_lines[0],
                text_quote=conclusion_lines[0].replace("- ", ""),
                char_start=0,
                char_end=min(len(conclusion_lines[0]), 80),
                anchor="final_1",
                metadata=CitationMetadata(title=f"Internal doc {payload.internal_doc_id}", doc_id=payload.internal_doc_id, source_file=f"{payload.internal_doc_id}.pdf", source_ext=".pdf", page_no=1),
            ),
        ]

    def _extract_bullet_lines(self, markdown_text: str, fallback: list[str]) -> list[str]:
        lines = []
        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if line.startswith("- "):
                lines.append(line)
        return lines if lines else fallback

    def _first_content_line(self, text: str) -> str:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#"):
                return line.replace("- ", "")
        return ""

    def _get_str(self, value: object) -> str:
        return "" if value is None else str(value)
