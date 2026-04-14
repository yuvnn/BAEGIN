import asyncio
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

TOP_TIER_LABS = [
    "Google", "Meta", "Microsoft", "OpenAI", "DeepMind",
    "Anthropic", "Stanford", "MIT", "CMU", "Berkeley",
    "Apple", "Amazon", "NVIDIA", "Hugging Face", "Allen Institute",
]

SEMAPHORE_LIMIT = 10
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
    if not data or "error" in data:
        return True  # fallback: don't drop on API failure

    authors = data.get("authors", [])
    for author in authors:
        affiliations = author.get("affiliations", [])
        for aff in affiliations:
            aff_name = aff if isinstance(aff, str) else aff.get("name", "")
            if any(lab.lower() in aff_name.lower() for lab in TOP_TIER_LABS):
                return True

    if data.get("influentialCitationCount", 0) > 0:
        return True

    return False


async def _fetch_one(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    paper: dict,
) -> dict:
    arxiv_id = _extract_arxiv_id(paper)
    if not arxiv_id:
        return {**paper, "_semantic_pass": True}

    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    async with semaphore:
        try:
            url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
            params = {"fields": "authors.affiliations,citationCount,influentialCitationCount"}
            resp = await client.get(url, params=params, headers=headers, timeout=10)
            await asyncio.sleep(0.3)
            if resp.status_code == 200:
                data = resp.json()
            else:
                logger.warning("Semantic Scholar API %d for arxiv:%s", resp.status_code, arxiv_id)
                data = {}
        except Exception as exc:
            logger.warning("Semantic Scholar fetch error for arxiv:%s: %s", arxiv_id, exc)
            data = {}

    passes = _passes_semantic(data)
    return {**paper, "_semantic_pass": passes}


async def _enrich_all(papers: list[dict]) -> list[dict]:
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    async with httpx.AsyncClient() as client:
        tasks = [_fetch_one(client, semaphore, p) for p in papers]
        return await asyncio.gather(*tasks)


def enrich_with_semantic_scholar(papers: list[dict]) -> list[dict]:
    """Stage 1.5: Filter using Semantic Scholar affiliation + citation data."""
    enriched = asyncio.run(_enrich_all(papers))
    result = [p for p in enriched if p.pop("_semantic_pass", True)]
    logger.info(
        "semantic_filter: %d → %d (top-tier lab affiliation or influential citations)",
        len(papers), len(result),
    )
    return result
