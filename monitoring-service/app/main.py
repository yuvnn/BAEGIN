import os
import time
from pathlib import Path

import requests
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

from .comparator import compare_with_internal_docs
from .monitor import fetch_mock_papers

app = FastAPI(title="monitoring-service", version="0.1.0")

INTERNAL_SERVICE_URL = os.getenv("INTERNAL_SERVICE_URL", "http://localhost:18084")
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
        detail="internal-service is not ready yet. Please retry in a few seconds.",
    ) from last_error


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "monitoring-service"}


@app.post("/monitor/run")
def run_monitoring(payload: MonitoringRequest) -> dict:
    papers = fetch_mock_papers(payload.keyword)

    for paper in papers:
        post_with_retry(
            f"{INTERNAL_SERVICE_URL}/ingest/paper",
            {
                "doc_id": paper["paper_id"],
                "title": paper["title"],
                "text": paper["abstract"],
            },
        )

    return {"keyword": payload.keyword, "fetched": len(papers), "papers": papers}


@app.post("/compare")
def compare(payload: CompareRequest) -> dict:
    result = compare_with_internal_docs(payload.query_text)
    return {
        "paper_id": payload.paper_id,
        "comparison": result,
        "report_hint": "Use this result as evidence input for LLM report generation.",
    }
