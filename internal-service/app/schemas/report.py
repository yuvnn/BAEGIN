from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReportSectionContent(BaseModel):
    overview_summary: str = ""
    internal_requirements_3lines: str = ""
    paper_tech_summary_3lines: str = ""
    mapping_analysis_table_md: str = ""
    candidate_technologies_10lines: str = ""
    integration_design_10lines: str = ""
    expected_impact_5lines: str = ""
    limitations_and_risks_5lines: str = ""
    final_conclusion_and_priorities_5lines: str = ""


class ReportDocument(BaseModel):
    title: str
    sections: ReportSectionContent


class CitationMetadata(BaseModel):
    title: Optional[str] = None
    doc_id: Optional[str] = None
    source_file: Optional[str] = None
    source_ext: Optional[str] = None
    category: Optional[str] = None
    paper_url: Optional[str] = None
    arxiv_categories: Optional[str] = None
    page_no: Optional[int] = None


class Citation(BaseModel):
    citation_id: str
    source_type: Literal["paper", "internal"]
    source_id: str
    source_text: str
    text_quote: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    anchor: str
    metadata: CitationMetadata = Field(default_factory=CitationMetadata)


class FinalResponse(BaseModel):
    report_id: str
    paper_id: str
    internal_doc_id: str
    status: Literal["running", "completed", "failed"]
    updated_at: str
    report: ReportDocument
    citations: list[Citation] = Field(default_factory=list)
