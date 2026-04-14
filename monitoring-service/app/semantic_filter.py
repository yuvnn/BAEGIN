import logging
import os
import re
import time

import requests

logger = logging.getLogger(__name__)

TOP_TIER_LABS = [
    "Google", "Meta", "Microsoft", "OpenAI", "DeepMind",
    "Anthropic", "Stanford", "MIT", "CMU", "Berkeley",
    "Apple", "Amazon", "NVIDIA", "Hugging Face", "Allen Institute",
]

_ARXIV_ID_RE = re.compile(r"\d{4}\.\d{4,5}")


def _extract_arxiv_id(paper: dict) -> str | None:
    paper_id = paper.get("paper_id", "")
    match = _ARXIV_ID_RE.search(paper_id)
    if match:
        return match.group()
    arxiv_id = paper.get("arxiv_id")
    if arxiv_id:
        match = _ARXIV_ID_RE.search(arxiv_id)
        if match:
            return match.group()
    return None


def _passes_semantic(data: dict) -> bool:
    if not data:
        return True  # fallback: don't drop on API failure

    authors = data.get("authors") or []
    for author in authors:
        affiliations = author.get("affiliations") or []
        for aff in affiliations:
            aff_name = aff if isinstance(aff, str) else (aff or {}).get("name", "")
            if aff_name and any(lab.lower() in aff_name.lower() for lab in TOP_TIER_LABS):
                return True

    if data.get("influentialCitationCount", 0) > 0:
        return True

    return False


def _fetch_one(paper: dict, headers: dict) -> dict:
    arxiv_id = _extract_arxiv_id(paper)
    if not arxiv_id:
        return {**paper, "_semantic_pass": True}

    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
        params = {"fields": "authors.affiliations,citationCount,influentialCitationCount"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
        elif resp.status_code == 404:
            logger.debug("Semantic Scholar: not indexed yet — pass arxiv:%s", arxiv_id)
            data = {}
        elif resp.status_code == 429:
            logger.warning("Semantic Scholar rate limit — pass arxiv:%s", arxiv_id)
            data = {}
        else:
            logger.warning("Semantic Scholar %d — pass arxiv:%s", resp.status_code, arxiv_id)
            data = {}
    except Exception as exc:
        logger.warning("Semantic Scholar error for arxiv:%s: %s — passing", arxiv_id, exc)
        data = {}

    return {**paper, "_semantic_pass": _passes_semantic(data)}


def enrich_with_semantic_scholar(papers: list[dict]) -> list[dict]:
    """Stage 1.5: Sequential requests with 0.5s delay to stay within rate limit."""
    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    enriched = []
    for paper in papers:
        enriched.append(_fetch_one(paper, headers))
        time.sleep(0.5)

    result = [p for p in enriched if p.pop("_semantic_pass", True)]
    logger.info(
        "semantic_filter: %d → %d (top-tier lab affiliation or influential citations)",
        len(papers), len(result),
    )
    return result
