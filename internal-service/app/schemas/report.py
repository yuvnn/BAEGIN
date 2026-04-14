from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .citation import Citation


class StageStatus(BaseModel):
    value: Literal["pending", "running", "completed", "failed"]


StageStatusValue = Literal["pending", "running", "completed", "failed"]


class StageResult(BaseModel):
    stage_no: int
    stage_name: str
    status: StageStatusValue = "pending"
    detail: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ReportSections(BaseModel):
    overview_summary: str
    internal_requirements_3lines: str
    paper_tech_summary_3lines: str
    mapping_analysis_table_md: str
    candidate_technologies_10lines: str
    integration_design_10lines: str
    expected_impact_5lines: str
    limitations_and_risks_5lines: str
    final_conclusion_and_priorities_5lines: str


class FinalReport(BaseModel):
    title: str
    sections: ReportSections


class FinalResponse(BaseModel):
    report_id: str = Field(default_factory=lambda: f"rep-{uuid4().hex[:12]}")
    paper_id: str
    internal_doc_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    current_stage: int = 1
    stages: list[StageResult] = Field(default_factory=list)
    report: FinalReport
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
