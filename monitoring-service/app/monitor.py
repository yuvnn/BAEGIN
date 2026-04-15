import logging
import re
import time
from datetime import datetime, timedelta
from typing import Optional

import arxiv
import requests

logger = logging.getLogger(__name__)

_ARXIV_ID_RE = re.compile(r"\d{4}\.\d{4,5}")

# 단일 클라이언트를 공유해 요청 간 딜레이가 누적 추적됨
# delay_seconds=5: 요청 사이 최소 5초 대기 (기본값 3초보다 보수적)
_ARXIV_CLIENT = arxiv.Client(page_size=100, delay_seconds=5, num_retries=3)

_ARXIV_CATEGORY_GROUPS = [
    ["cat:cs.AI"],
    ["cat:cs.LG", "cat:cs.CL"],
    ["cat:cs.CV", "cat:cs.RO"],
    ["cat:cs.MA", "cat:cs.CY", "cat:stat.ML"],
]


def _fetch_arxiv_group(
    categories: list[str] | None = None,
    date_filter: str = "",
    max_results: int = 50,
    query_string: str | None = None,
) -> list[dict]:
    if query_string:
        query = query_string
    else:
        query = " OR ".join(categories or [])
        if date_filter:
            query = f"({query}) AND submittedDate:[{date_filter} TO *]"

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    try:
        for result in _ARXIV_CLIENT.results(search):
            entry_id = result.entry_id
            match = _ARXIV_ID_RE.search(entry_id)
            arxiv_id = match.group() if match else entry_id

            pdf_url = None
            try:
                pdf_url = result.pdf_url
            except Exception:
                pass

            papers.append(
                {
                    "paper_id": f"arxiv:{arxiv_id}",
                    "title": result.title,
                    "abstract": result.summary,
                    "authors": [a.name for a in result.authors],
                    "published_at": result.published.isoformat(),
                    "source": "arxiv",
                    "url": result.entry_id,
                    "pdf_url": pdf_url,
                    "categories": result.categories,
                    "arxiv_categories": result.categories,  # metadata_filter 호환
                    "comment": result.comment or "",
                }
            )
    except Exception as exc:
        logger.warning("arXiv fetch error for %s: %s — skipping group", categories, exc)
    return papers


def fetch_arxiv_ai_papers(
    last_run_dt: datetime | None = None, max_results: int = 1000
) -> list[dict]:
    # 항상 최근 7일 윈도우 사용 — last_run_dt가 오늘이면 arXiv가 500 반환함
    # dedup은 seen_papers.json이 담당
    window_start = datetime.utcnow() - timedelta(days=7)
    date_filter = window_start.strftime("%Y%m%d0000")
    per_group = max(max_results // len(_ARXIV_CATEGORY_GROUPS), 50)

    seen_ids: set[str] = set()
    papers = []
    for i, group in enumerate(_ARXIV_CATEGORY_GROUPS):
        if i > 0:
            time.sleep(10)  # 그룹 간 10초 대기 — 429 방지
        group_papers = _fetch_arxiv_group(group, date_filter, per_group)
        for p in group_papers:
            if p["paper_id"] not in seen_ids:
                seen_ids.add(p["paper_id"])
                papers.append(p)
        logger.info("arXiv group %s: %d papers", group, len(group_papers))

    return papers


def fetch_hf_papers() -> list[dict]:
    try:
        response = requests.get(
            "https://huggingface.co/api/daily_papers", timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error("HuggingFace Papers fetch error: %s", exc)
        return []

    papers = []
    for item in data:
        paper = item.get("paper", {})
        title = paper.get("title", "")
        abstract = paper.get("summary", "")

        raw_id = paper.get("id", "")
        arxiv_id = paper.get("arxivId") or (
            raw_id if _ARXIV_ID_RE.fullmatch(raw_id) else None
        )

        if arxiv_id:
            paper_id = f"arxiv:{arxiv_id}"
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
            url = f"https://arxiv.org/abs/{arxiv_id}"
        else:
            paper_id = f"hf:{raw_id}"
            pdf_url = None
            url = f"https://huggingface.co/papers/{raw_id}"

        papers.append(
            {
                "paper_id": paper_id,
                "title": title,
                "abstract": abstract,
                "authors": [a.get("name", "") for a in paper.get("authors", [])],
                "published_at": paper.get(
                    "publishedAt", datetime.utcnow().isoformat()
                ),
                "source": "huggingface",
                "url": url,
                "pdf_url": pdf_url,
                "arxiv_id": arxiv_id,
                "upvotes": paper.get("upvotes", 0),
            }
        )
    return papers


def fetch_all_ai_papers(
    last_run_dt: datetime | None = None, max_results: int = 1000
) -> list[dict]:
    papers: list[dict] = []
    papers.extend(fetch_arxiv_ai_papers(last_run_dt, max_results))
    papers.extend(fetch_hf_papers())
    return papers


def search_papers_custom(
    categories: list[str],
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    keywords: list[str] = [],
    max_results: int = 50,
) -> list[dict]:
    """커스텀 파라미터로 arXiv 직접 검색."""
    cat_q = " OR ".join(f"cat:{c}" for c in categories) if categories \
            else "cat:cs.AI OR cat:cs.LG"

    if date_from and date_to:
        date_q = f"submittedDate:[{date_from.replace('-','')}0000 TO {date_to.replace('-','')}2359]"
    elif date_from:
        date_q = f"submittedDate:[{date_from.replace('-','')}0000 TO *]"
    else:
        w = (datetime.utcnow() - timedelta(days=30)).strftime("%Y%m%d0000")
        date_q = f"submittedDate:[{w} TO *]"

    kw_q = " OR ".join(f"all:{k}" for k in keywords) if keywords else ""
    parts = [f"({cat_q})", date_q]
    if kw_q:
        parts.append(f"({kw_q})")
    query = " AND ".join(parts)

    return _fetch_arxiv_group(query_string=query, max_results=max_results)
