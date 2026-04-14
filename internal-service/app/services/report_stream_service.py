from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..repositories.internal_doc_repository import get_internal_doc
from ..repositories.paper_repository import get_paper_summary
from ..schemas.input import GenerateReportRequest
from ..schemas.citation import Citation
from ..schemas.report import FinalResponse
from ..services.citation_service import normalize_citations
from ..services.pipeline_service import PipelineService


SECTION_SPECS: list[dict[str, str]] = [
    {
        "section_code": "internal_requirements_3lines",
        "section_title": "기획서 핵심 요구사항",
        "content_type": "text/plain",
    },
    {
        "section_code": "paper_tech_summary_3lines",
        "section_title": "논문 핵심 기술 요약",
        "content_type": "text/plain",
    },
    {
        "section_code": "mapping_analysis_table_md",
        "section_title": "기획서-논문 매핑 분석 (raw)",
        "content_type": "text/markdown",
    },
    {
        "section_code": "candidate_technologies_10lines",
        "section_title": "접목 가능한 기술 후보",
        "content_type": "text/plain",
    },
    {
        "section_code": "integration_design_10lines",
        "section_title": "도입 방식 설계",
        "content_type": "text/plain",
    },
    {
        "section_code": "expected_impact_5lines",
        "section_title": "기대 효과",
        "content_type": "text/plain",
    },
    {
        "section_code": "limitations_and_risks_5lines",
        "section_title": "한계와 리스크",
        "content_type": "text/plain",
    },
    {
        "section_code": "final_conclusion_and_priorities_5lines",
        "section_title": "종합 결론 및 우선순위",
        "content_type": "text/plain",
    },
]


def _build_five_line_summary(summary_md: str, max_lines: int = 5) -> list[str]:
    lines: list[str] = []
    for raw_line in summary_md.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        line = line.replace("**", "").strip()
        if line:
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return lines


@dataclass
class ReportGenerationJob:
    report_id: str
    paper_id: str
    internal_doc_id: str
    events: list[dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    failed: bool = False
    condition: threading.Condition = field(default_factory=threading.Condition)


class ReportStreamService:
    def __init__(self, pipeline_service: PipelineService | None = None) -> None:
        self.pipeline_service = pipeline_service or PipelineService()
        self._jobs: dict[str, ReportGenerationJob] = {}
        self._lock = threading.Lock()

    def start_generation(self, payload: GenerateReportRequest) -> str:
        report_id = f"rep-{uuid4().hex[:12]}"
        job = ReportGenerationJob(
            report_id=report_id,
            paper_id=payload.paper_id,
            internal_doc_id=payload.internal_doc_id,
        )
        with self._lock:
            self._jobs[report_id] = job

        for spec in SECTION_SPECS:
            self._append_event(
                job,
                "section_update",
                {
                    "report_id": report_id,
                    "section_code": spec["section_code"],
                    "section_title": spec["section_title"],
                    "status": "running",
                    "content": "",
                    "content_type": spec["content_type"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        worker = threading.Thread(target=self._run_generation, args=(job,), daemon=True)
        worker.start()
        return report_id

    def get_job(self, report_id: str) -> ReportGenerationJob | None:
        with self._lock:
            return self._jobs.get(report_id)

    def _append_event(self, job: ReportGenerationJob, event_name: str, payload: dict[str, Any]) -> None:
        with job.condition:
            job.events.append({"event": event_name, "data": payload})
            job.condition.notify_all()

    def _run_generation(self, job: ReportGenerationJob) -> None:
        try:
            paper_summary = get_paper_summary(job.paper_id)
            internal_doc = get_internal_doc(job.internal_doc_id)
            analysis_result = self.pipeline_service.run_analysis_agent(
                paper_summary=paper_summary,
                internal_doc=internal_doc,
            )

            internal_lines = [item.requirement_text for item in analysis_result.internal_requirements[:3]]
            paper_lines = _build_five_line_summary(paper_summary.summary_md, max_lines=5)

            mapping_rows = [
                "| 요구사항 id | 요구사항 | 기술 id | 기술 설명 | 적합도 | 매핑 근거 |",
                "|-------------|----------|---------|-----------|--------|-----------|",
            ]
            for row in analysis_result.mapping_table:
                req_text = next(
                    (req.requirement_text for req in analysis_result.internal_requirements if req.requirement_id == row.requirement_id),
                    "",
                )
                tech_text = next(
                    (tech.technology_text for tech in analysis_result.paper_technologies if tech.technology_id == row.technology_id),
                    "",
                )
                mapping_rows.append(
                    f"| {row.requirement_id} | {req_text} | {row.technology_id} | {tech_text} | {row.match_score:.2f} | {row.rationale} |"
                )

            early_sections: dict[str, str] = {
                "internal_requirements_3lines": "\n".join(internal_lines) if internal_lines else "요구사항 데이터 없음",
                "paper_tech_summary_3lines": "\n".join(paper_lines) if paper_lines else "논문 기술 데이터 없음",
                "mapping_analysis_table_md": "\n".join(mapping_rows),
            }

            for spec in SECTION_SPECS[:3]:
                section_code = spec["section_code"]
                self._append_event(
                    job,
                    "section_update",
                    {
                        "report_id": job.report_id,
                        "section_code": section_code,
                        "section_title": spec["section_title"],
                        "status": "completed",
                        "content": early_sections.get(section_code, ""),
                        "content_type": spec["content_type"],
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

            final_response = self.pipeline_service.run_report_agent(analysis_result=analysis_result)
            final_response.report.sections.paper_tech_summary_3lines = (
                "\n".join(paper_lines) if paper_lines else "논문 기술 데이터 없음"
            )

            # Keep analysis citations as authoritative source when report agent omits them.
            if not final_response.citations:
                final_response.citations = analysis_result.citations

            if not any(c.source_type == "paper" for c in final_response.citations):
                final_response.citations.append(
                    Citation(
                        citation_id=f"c-paper-fallback-{job.report_id}",
                        source_type="paper",
                        source_id=paper_summary.paper_id,
                        source_text=paper_summary.summary_md,
                        text_quote=None,
                        anchor="paper_tech_1",
                        metadata={
                            "title": paper_summary.title,
                            "paper_url": paper_summary.paper_url,
                            "category": paper_summary.category,
                        },
                    )
                )

            first_internal_chunk = internal_doc.internal_chunks[0] if internal_doc.internal_chunks else None
            paper_anchor_idx = 1
            internal_anchor_idx = 1
            for citation in final_response.citations:
                if citation.source_type == "paper":
                    # Always expose full paper markdown for consistent summary rendering on UI.
                    citation.source_text = paper_summary.summary_md
                    if not citation.metadata:
                        citation.metadata = {}
                    citation.metadata.setdefault("paper_url", paper_summary.paper_url)
                    citation.metadata.setdefault("title", paper_summary.title)
                    citation.metadata.setdefault("category", paper_summary.category)
                    if not citation.anchor:
                        citation.anchor = f"paper_tech_{paper_anchor_idx}"
                    paper_anchor_idx += 1

                if citation.source_type == "internal" and first_internal_chunk is not None:
                    if not citation.metadata:
                        citation.metadata = {}
                    citation.metadata.setdefault("doc_id", first_internal_chunk.metadata.doc_id)
                    citation.metadata.setdefault("source_file", first_internal_chunk.metadata.source_file)
                    citation.metadata.setdefault("source_ext", first_internal_chunk.metadata.source_ext)
                    citation.metadata.setdefault("title", first_internal_chunk.metadata.title)
                    if not citation.anchor:
                        citation.anchor = f"int_req_{internal_anchor_idx}"
                    internal_anchor_idx += 1

            final_response.citations = normalize_citations(final_response.citations)
            final_response.report_id = job.report_id
            final_response.paper_id = job.paper_id
            final_response.internal_doc_id = job.internal_doc_id
            now = datetime.now(timezone.utc)
            final_response.status = "completed"
            final_response.current_stage = 5
            if final_response.created_at is None:
                final_response.created_at = now
            final_response.updated_at = now
            self.pipeline_service.storage_service.save(final_response)

            sections = final_response.report.sections.model_dump()
            for spec in SECTION_SPECS[3:]:
                section_code = spec["section_code"]
                self._append_event(
                    job,
                    "section_update",
                    {
                        "report_id": job.report_id,
                        "section_code": section_code,
                        "section_title": spec["section_title"],
                        "status": "completed",
                        "content": sections.get(section_code, ""),
                        "content_type": spec["content_type"],
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )

            self._append_event(
                job,
                "completed",
                {
                    "report_id": job.report_id,
                    "status": "completed",
                    "report": final_response.model_dump(mode="json"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            with job.condition:
                job.completed = True
                job.condition.notify_all()
        except Exception as exc:
            self._append_event(
                job,
                "failed",
                {
                    "report_id": job.report_id,
                    "status": "failed",
                    "message": str(exc),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            with job.condition:
                job.failed = True
                job.completed = True
                job.condition.notify_all()

    @staticmethod
    def to_sse_message(event_name: str, data: dict[str, Any]) -> str:
        return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
