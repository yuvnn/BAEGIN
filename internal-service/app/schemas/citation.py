from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["internal", "paper"]


class Citation(BaseModel):
    citation_id: str = Field(..., min_length=1)
    source_type: SourceType
    source_id: str = Field(..., min_length=1)
    source_text: str = Field(..., min_length=1)
    text_quote: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    anchor: str | None = None
    metadata: dict[str, str | int | None] = Field(default_factory=dict)
