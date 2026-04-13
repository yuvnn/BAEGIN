import logging
import re
from datetime import datetime

import arxiv
import requests

logger = logging.getLogger(__name__)

_ARXIV_ID_RE = re.compile(r"\d{4}\.\d{4,5}")


def fetch_arxiv_papers(
    keyword: str, last_run_dt: datetime | None = None, max_results: int = 10
) -> list[dict]:
    query = keyword
    if last_run_dt:
        date_str = last_run_dt.strftime("%Y%m%d%H%M")
        query = f"{keyword} AND submittedDate:[{date_str} TO *]"

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    try:
        for result in client.results(search):
            entry_id = result.entry_id  # e.g. https://arxiv.org/abs/2404.12345v1
            match = _ARXIV_ID_RE.search(entry_id)
            arxiv_id = match.group() if match else entry_id

            pdf_url = None
            try:
                pdf_url = result.pdf_url  # provided by arxiv library
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
                }
            )
    except Exception as exc:
        logger.error("arXiv fetch error: %s", exc)
    return papers


def fetch_hf_papers(keyword: str | None = None) -> list[dict]:
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

        if keyword:
            kw = keyword.lower()
            if kw not in title.lower() and kw not in abstract.lower():
                continue

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
            }
        )
    return papers


def fetch_papers(
    keyword: str,
    source: str = "all",
    last_run_dt: datetime | None = None,
    max_results: int = 10,
) -> list[dict]:
    papers: list[dict] = []
    if source in ("arxiv", "all"):
        papers.extend(fetch_arxiv_papers(keyword, last_run_dt, max_results))
    if source in ("huggingface", "all"):
        papers.extend(fetch_hf_papers(keyword))
    return papers
