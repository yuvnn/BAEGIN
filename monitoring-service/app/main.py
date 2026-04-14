import logging
import os
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

from .comparator import compare_with_internal_docs
from .impact_agent import IMPACT_THRESHOLD, score_papers
from .kafka_producer import kafka_publisher
from .metadata_filter import filter_by_metadata
from .monitor import fetch_all_ai_papers
from .semantic_filter import enrich_with_semantic_scholar
from .seen_papers import is_new, load_state, mark_seen, save_state, to_canonical_id

logger = logging.getLogger(__name__)

INTERNAL_SERVICE_URL = os.getenv("INTERNAL_SERVICE_URL", "http://localhost:18084")
PAPER_SERVICE_URL = os.getenv("PAPER_SERVICE_URL", "http://localhost:18083")
MONITOR_INTERVAL_MINUTES = int(os.getenv("MONITOR_INTERVAL_MINUTES", "180"))

REPORT_DIR = Path("/app/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

scheduler = BackgroundScheduler()

CATEGORY_GROUPS = {
    "Language & Text":    ["cs.CL"],
    "Vision & Graphics":  ["cs.CV"],
    "Robotics & Control": ["cs.RO"],
    "ML Foundation":      ["cs.LG", "cs.AI", "stat.ML"],
    "Multi-Agent & RL":   ["cs.MA"],
    "Ethics & Society":   ["cs.CY"],
}


def apply_diversity_quota(
    all_scored: list[dict],
    high_impact: list[dict],
    groups: dict[str, list[str]],
) -> list[dict]:
    """Ensure at least one paper per category group in the final selection."""
    result = list(high_impact)
    result_ids = {to_canonical_id(p) for p in result}

    for group_name, categories in groups.items():
        # Check if any paper in result already covers this group
        group_covered = any(
            set(p.get("categories", [])) & set(categories)
            for p in result
        )
        if group_covered:
            continue

        # Find best-scoring paper in all_scored for this group not yet included
        candidates = [
            p for p in all_scored
            if set(p.get("categories", [])) & set(categories)
            and to_canonical_id(p) not in result_ids
        ]
        if not candidates:
            continue

        best = max(candidates, key=lambda p: p.get("impact_score", 0))
        result.append(best)
        result_ids.add(to_canonical_id(best))
        logger.info(
            "Diversity quota: added '%s' for group '%s' (score=%d)",
            best.get("title", "")[:60], group_name, best.get("impact_score", 0),
        )

    return result


def _run_scheduled_monitoring() -> None:
    state = load_state()
    last_run_dt: datetime | None = state.get("last_run")
    now = datetime.utcnow()

    # 1. Collect
    papers = fetch_all_ai_papers(last_run_dt, max_results=1000)
    logger.info("Collected: %d papers", len(papers))

    # 2. Dedup
    new_papers = [p for p in papers if is_new(to_canonical_id(p), state)]
    logger.info("After dedup: %d", len(new_papers))

    # 3. Stage 1: Metadata Filter
    filtered = filter_by_metadata(new_papers)
    logger.info("After metadata filter: %d", len(filtered))

    # 4. Stage 1.5: Semantic Scholar Filter
    enriched = enrich_with_semantic_scholar(filtered)
    logger.info("After semantic filter: %d", len(enriched))

    # 5. Stage 2: Impact Agent
    scored = score_papers(enriched)
    high_impact = [p for p in scored if p.get("impact_score", 0) >= IMPACT_THRESHOLD]
    logger.info("High-impact papers: %d", len(high_impact))

    # 6. Diversity quota: ensure at least one paper per category group
    quota_papers = apply_diversity_quota(scored, high_impact, CATEGORY_GROUPS)
    logger.info("After diversity quota: %d", len(quota_papers))

    # 7. Publish & ingest
    for paper in quota_papers:
        cid = to_canonical_id(paper)
        _ingest_paper(paper)
        kafka_publisher.publish(paper)
        mark_seen(cid, state)

    # Mark ALL new papers as seen (prevent re-processing)
    for paper in new_papers:
        mark_seen(to_canonical_id(paper), state)

    state["last_run"] = now
    save_state(state)


def _ingest_paper(paper: dict) -> None:
    try:
        post_with_retry(
            f"{INTERNAL_SERVICE_URL}/ingest/paper",
            {
                "doc_id": paper["paper_id"],
                "title": paper["title"],
                "text": paper["abstract"],
            },
        )
    except HTTPException as exc:
        logger.warning("Ingest failed for paper_id=%s: %s", paper["paper_id"], exc.detail)


@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka_publisher.connect()
    scheduler.add_job(
        _run_scheduled_monitoring,
        "interval",
        minutes=MONITOR_INTERVAL_MINUTES,
        id="scheduled_monitoring",
    )
    scheduler.start()
    logger.info("Scheduler started (interval=%d min).", MONITOR_INTERVAL_MINUTES)
    yield
    scheduler.shutdown(wait=False)
    kafka_publisher.close()
    logger.info("Scheduler stopped.")


app = FastAPI(title="monitoring-service", version="0.1.0", lifespan=lifespan)


class MonitoringRequest(BaseModel):
    max_results: int = 1000


class CompareRequest(BaseModel):
    paper_id: str
    query_text: str


def post_with_retry(
    url: str, payload: dict, attempts: int = 5, delay: float = 1.0
) -> requests.Response:
    last_error: requests.RequestException | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(delay)

    raise HTTPException(
        status_code=503,
        detail="internal-service is not ready yet. Please retry in a few seconds.",
    ) from last_error


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "monitoring-service"}


@app.post("/monitor/run")
def run_monitoring(payload: MonitoringRequest) -> dict:
    state = load_state()
    last_run_dt: datetime | None = state.get("last_run")

    papers = fetch_all_ai_papers(last_run_dt, max_results=payload.max_results)
    new_papers = [p for p in papers if is_new(to_canonical_id(p), state)]

    filtered = filter_by_metadata(new_papers)
    enriched = enrich_with_semantic_scholar(filtered)
    scored = score_papers(enriched)
    high_impact = [p for p in scored if p.get("impact_score", 0) >= IMPACT_THRESHOLD]
    quota_papers = apply_diversity_quota(scored, high_impact, CATEGORY_GROUPS)

    published = 0
    ingested = 0
    for paper in quota_papers:
        cid = to_canonical_id(paper)
        _ingest_paper(paper)
        ingested += 1
        if kafka_publisher.publish(paper):
            published += 1
        mark_seen(cid, state)

    for paper in new_papers:
        mark_seen(to_canonical_id(paper), state)

    state["last_run"] = datetime.utcnow()
    save_state(state)

    return {
        "collected": len(papers),
        "after_dedup": len(new_papers),
        "after_metadata_filter": len(filtered),
        "after_semantic_filter": len(enriched),
        "high_impact": len(high_impact),
        "published": len(quota_papers),
        "kafka_published": published,
        "papers": quota_papers,
    }


@app.post("/compare")
def compare(payload: CompareRequest) -> dict:
    result = compare_with_internal_docs(payload.query_text)
    return {
        "paper_id": payload.paper_id,
        "comparison": result,
        "report_hint": "Use this result as evidence input for LLM report generation.",
    }
