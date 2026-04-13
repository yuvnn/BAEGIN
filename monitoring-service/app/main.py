import os
import logging
from pathlib import Path

import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from .comparator import compare_with_internal_docs
from .monitor import fetch_mock_papers
from .evaluator import evaluate_paper

logger = logging.getLogger(__name__)

app = FastAPI(title="monitoring-service", version="0.1.0")

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://localhost:18084")
REPORT_DIR = Path("/app/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class MonitoringRequest(BaseModel):
    keyword: str


class CompareRequest(BaseModel):
    paper_id: str
    query_text: str


def process_monitoring_task(keyword: str):
    logger.info(f"Starting background monitoring task for keyword: {keyword}")
    papers = fetch_mock_papers(keyword)

    for paper in papers:
        logger.info(f"Evaluating paper: {paper['title']}")
        evaluation = evaluate_paper(keyword, paper["title"], paper["abstract"])
        
        if evaluation.is_relevant:
            logger.info(f"Paper '{paper['title']}' passed with score {evaluation.score}. Ingesting...")
            try:
                requests.post(
                    f"{PDF_SERVICE_URL}/ingest/paper",
                    json={
                        "doc_id": paper["paper_id"],
                        "title": paper["title"],
                        "text": paper["abstract"],
                        "metadata": {
                            "evaluation_score": evaluation.score,
                            "evaluation_review": evaluation.review
                        }
                    },
                    timeout=10,
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
