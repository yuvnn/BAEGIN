from __future__ import annotations

from pydantic import BaseModel, Field

from .citation import Citation


class InternalRequirement(BaseModel):
    requirement_id: str
    requirement_text: str
    priority: str = "medium"
    citations: list[Citation] = Field(default_factory=list)


class PaperTechnology(BaseModel):
    technology_id: str
    technology_text: str
    maturity: str = "unknown"
    citations: list[Citation] = Field(default_factory=list)


class MappingRow(BaseModel):
    row_id: str
    requirement_id: str
    technology_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    applicability: str
    citations: list[Citation] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    paper_id: str
    internal_doc_id: str
    internal_requirements: list[InternalRequirement] = Field(default_factory=list)
    paper_technologies: list[PaperTechnology] = Field(default_factory=list)
    mapping_table: list[MappingRow] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
