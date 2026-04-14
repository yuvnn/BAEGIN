import logging
import re
from datetime import datetime

import arxiv
import requests

logger = logging.getLogger(__name__)

_ARXIV_ID_RE = re.compile(r"\d{4}\.\d{4,5}")

_ARXIV_CATEGORY_GROUPS = [
    ["cat:cs.AI"],
    ["cat:cs.LG", "cat:cs.CL"],
    ["cat:cs.CV", "cat:cs.RO"],
    ["cat:cs.MA", "cat:cs.CY", "cat:stat.ML"],
]


def _fetch_arxiv_group(
    categories: list[str],
    date_filter: str,
    max_results: int,
) -> list[dict]:
    query = " OR ".join(categories)
    if date_filter:
        query = f"({query}) AND submittedDate:[{date_filter} TO *]"

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    try:
        for result in client.results(search):
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
                    "comment": result.comment or "",
                }
            )
    except Exception as exc:
        logger.warning("arXiv fetch error for %s: %s — skipping group", categories, exc)
    return papers


def fetch_arxiv_ai_papers(
    last_run_dt: datetime | None = None, max_results: int = 1000
) -> list[dict]:
    date_filter = last_run_dt.strftime("%Y%m%d0000") if last_run_dt else ""
    per_group = max(max_results // len(_ARXIV_CATEGORY_GROUPS), 50)

    seen_ids: set[str] = set()
    papers = []
    for group in _ARXIV_CATEGORY_GROUPS:
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
