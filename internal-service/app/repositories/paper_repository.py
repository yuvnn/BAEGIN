from __future__ import annotations

import logging
import os

import httpx

from ..schemas.input import PaperSummary

logger = logging.getLogger(__name__)
PAPER_SERVICE_URL = os.getenv("PAPER_SERVICE_URL", "http://localhost:18083")

_MOCK_PAPERS: dict[str, PaperSummary] = {
    "paper-demo-001": PaperSummary(
        paper_id="paper-demo-001",
        title="Demo Paper",
        summary_md="Demo summary for testing.",
        paper_url="https://arxiv.org/pdf/2504.08626",
        authors=["Demo Author"],
        category="ML Foundation",
    ),
}


def get_paper_summary(paper_id: str) -> PaperSummary:
    if paper_id in _MOCK_PAPERS:
        return _MOCK_PAPERS[paper_id]

    try:
        resp = httpx.get(f"{PAPER_SERVICE_URL}/papers/{paper_id}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return PaperSummary(
            paper_id=data["paper_id"],
            title=data.get("title") or data.get("paper_id", paper_id),
            summary_md=(
                data.get("md_summary")
                or (data.get("summary_data") or {}).get("summary")
                or data.get("abstract")
                or ""
            ),
            paper_url=data.get("paper_url") or data.get("url") or "",
            authors=data.get("authors") or [],
            category=(data.get("category") or data.get("metadata", {}).get("category") or "Unknown"),
        )
    except Exception as exc:
        logger.warning("[paper_repository] failed to fetch paper_id=%s: %s", paper_id, exc)
        return PaperSummary(
            paper_id=paper_id,
            title=f"Paper {paper_id}",
            summary_md="논문 데이터를 가져올 수 없어 기본값을 반환합니다.",
            paper_url="",
            authors=[],
            category="Unknown",
        )
