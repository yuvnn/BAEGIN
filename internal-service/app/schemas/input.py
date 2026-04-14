from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    paper_id: str = Field(..., min_length=1)
    internal_doc_id: str = Field(..., min_length=1)
