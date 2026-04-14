from __future__ import annotations

from datetime import datetime, timezone

from ..agents.analysis_agent import AnalysisAgent
from ..agents.report_agent import ReportAgent
from ..repositories.internal_doc_repository import get_internal_doc
from ..repositories.paper_repository import get_paper_summary
from ..services.citation_service import normalize_citations
from ..services.report_storage_service import ReportStorageService
from ..schemas.analysis import AnalysisResult
from ..schemas.input import InternalDoc, PaperSummary
from ..schemas.report import FinalResponse


class PipelineService:
    def __init__(
        self,
        analysis_agent: AnalysisAgent | None = None,
        report_agent: ReportAgent | None = None,
        storage_service: ReportStorageService | None = None,
    ) -> None:
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.report_agent = report_agent or ReportAgent()
        self.storage_service = storage_service or ReportStorageService()

    def run_analysis_agent(self, paper_summary: PaperSummary, internal_doc: InternalDoc) -> AnalysisResult:
        return self.analysis_agent.invoke(paper_summary=paper_summary, internal_doc=internal_doc)

    def run_report_agent(self, analysis_result: AnalysisResult) -> FinalResponse:
        return self.report_agent.invoke(analysis=analysis_result)

    def run_full_pipeline(self, paper_id: str, internal_doc_id: str, report_id: str | None = None) -> FinalResponse:
        paper_summary = get_paper_summary(paper_id)
        internal_doc = get_internal_doc(internal_doc_id)

        analysis_result = self.run_analysis_agent(paper_summary=paper_summary, internal_doc=internal_doc)
        final_response = self.run_report_agent(analysis_result=analysis_result)

        final_response.citations = normalize_citations(final_response.citations)

        now = datetime.now(timezone.utc)
        if report_id:
            final_response.report_id = report_id
        final_response.status = "completed"
        final_response.current_stage = 5
        if final_response.created_at is None:
            final_response.created_at = now
        final_response.updated_at = now

        self.storage_service.save(final_response)
        return final_response


if __name__ == "__main__":
    service = PipelineService()
    response = service.run_full_pipeline("paper-demo-001", "internal-demo-001")
    print(response.model_dump_json(indent=2, ensure_ascii=False))
