from __future__ import annotations

from pydantic import BaseModel, Field


class PaperSummary(BaseModel):
    paper_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    summary_md: str = Field(default="")
    paper_url: str = Field(default="")
    authors: list[str] = Field(default_factory=list)
    category: str = Field(default="unknown")


class InternalChunkMetadata(BaseModel):
    doc_id: str
    source_type: str = "internal"
    title: str
    source_file: str
    source_ext: str
    chunk_index: int
    doc_version: str = "v1"
    page_no: int | None = None
    chunk_char_start: int | None = None
    chunk_char_end: int | None = None


class InternalChunk(BaseModel):
    chunk_id: str
    document: str
    metadata: InternalChunkMetadata


class InternalDoc(BaseModel):
    internal_doc_id: str
    internal_doc_title: str
    internal_chunks: list[InternalChunk] = Field(default_factory=list)


class GenerateReportRequest(BaseModel):
    paper_id: str
    internal_doc_id: str
