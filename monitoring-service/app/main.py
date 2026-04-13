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
from .kafka_producer import kafka_publisher
from .monitor import fetch_papers
from .seen_papers import is_new, load_state, mark_seen, save_state, to_canonical_id

logger = logging.getLogger(__name__)

INTERNAL_SERVICE_URL = os.getenv("INTERNAL_SERVICE_URL", "http://localhost:18084")
PAPER_SERVICE_URL = os.getenv("PAPER_SERVICE_URL", "http://localhost:18083")
MONITOR_INTERVAL_MINUTES = int(os.getenv("MONITOR_INTERVAL_MINUTES", "60"))

REPORT_DIR = Path("/app/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

scheduler = BackgroundScheduler()


def _fetch_rules() -> list[dict]:
    """Fetch enroll rules from paper-service. Returns [] on failure."""
    try:
        resp = requests.get(f"{PAPER_SERVICE_URL}/rules", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch rules from paper-service: %s — skipping run", exc)
        return []


def _run_scheduled_monitoring() -> None:
    rules = _fetch_rules()
    if not rules:
        logger.info("No rules returned from paper-service; skipping scheduled run.")
        return

    state = load_state()
    last_run_dt: datetime | None = state.get("last_run")
    now = datetime.utcnow()

    logger.info("Scheduled monitoring started for %d rule(s)", len(rules))
    for rule in rules:
        keyword = rule.get("keyword", "").strip()
        source = rule.get("source", "all")
        if not keyword:
            continue
        try:
            papers = fetch_papers(keyword, source=source, last_run_dt=last_run_dt)
            new_count = 0
            for paper in papers:
                cid = to_canonical_id(paper)
                if not is_new(cid, state):
                    continue
                _ingest_paper(paper)
                kafka_publisher.publish(paper, keyword=keyword)
                mark_seen(cid, state)
                new_count += 1
            logger.info(
                "Scheduled: keyword=%s source=%s fetched=%d new=%d",
                keyword, source, len(papers), new_count,
            )
        except Exception as exc:
            logger.error("Scheduled monitoring error for keyword=%s: %s", keyword, exc)

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
    keyword: str
    max_results: int = 10
    source: str = "all"


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
    papers = fetch_papers(payload.keyword, source=payload.source)

    published = 0
    ingested = 0
    for paper in papers:
        cid = to_canonical_id(paper)
        if not is_new(cid, state):
            continue
        _ingest_paper(paper)
        ingested += 1
        if kafka_publisher.publish(paper, keyword=payload.keyword):
            published += 1
        mark_seen(cid, state)

    state["last_run"] = datetime.utcnow()
    save_state(state)

    return {
        "keyword": payload.keyword,
        "source": payload.source,
        "fetched": len(papers),
        "new": ingested,
        "kafka_published": published,
        "papers": [p for p in papers if to_canonical_id(p) in state["seen_ids"]],
    }


@app.post("/compare")
def compare(payload: CompareRequest) -> dict:
    result = compare_with_internal_docs(payload.query_text)
    return {
        "paper_id": payload.paper_id,
        "comparison": result,
        "report_hint": "Use this result as evidence input for LLM report generation.",
    }
