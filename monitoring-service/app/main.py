import os
import logging
import time
from pathlib import Path

import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

from .comparator import compare_with_internal_docs
from .monitor import fetch_mock_papers
from .evaluator import evaluate_paper

logger = logging.getLogger(__name__)

app = FastAPI(title="monitoring-service", version="0.1.0")

COMPARE_PDF_SERVICE_URL = os.getenv("COMPARE_PDF_SERVICE_URL", "http://localhost:18084")
REPORT_DIR = Path("/app/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class MonitoringRequest(BaseModel):
    keyword: str


class CompareRequest(BaseModel):
    paper_id: str
    query_text: str


def post_with_retry(url: str, payload: dict, attempts: int = 5, delay: float = 1.0) -> requests.Response:
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
        detail="comparepdf-service is not ready yet. Please retry in a few seconds.",
    ) from last_error


def process_monitoring_task(keyword: str):
    logger.info(f"Starting background monitoring task for keyword: {keyword}")
    papers = fetch_mock_papers(keyword)

    for paper in papers:
        logger.info(f"Evaluating paper: {paper['title']}")
        evaluation = evaluate_paper(keyword, paper["title"], paper["abstract"])
        
        if evaluation.is_relevant:
            logger.info(f"Paper '{paper['title']}' passed with score {evaluation.score}. Ingesting...")
            try:
                post_with_retry(
                    f"{COMPARE_PDF_SERVICE_URL}/ingest/paper",
                    {
                        "doc_id": paper["paper_id"],
                        "title": paper["title"],
                        "text": paper["abstract"],
                        "metadata": {
                            "evaluation_score": evaluation.score,
                            "evaluation_review": evaluation.review
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Failed to ingest paper '{paper['title']}': {e}")
        else:
            logger.info(f"Paper '{paper['title']}' rejected with score {evaluation.score}. Reason: {evaluation.review}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "monitoring-service"}


@app.post("/monitor/run")
def run_monitoring(payload: MonitoringRequest, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(process_monitoring_task, payload.keyword)
    return {"keyword": payload.keyword, "status": "Background task started"}


@app.post("/compare")
def compare(payload: CompareRequest) -> dict:
    result = compare_with_internal_docs(payload.query_text)
    return {
        "paper_id": payload.paper_id,
        "comparison": result,
        "report_hint": "Use this result as evidence input for LLM report generation.",
    }
