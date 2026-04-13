import os
from pathlib import Path

import requests
from fastapi import FastAPI
from pydantic import BaseModel

from .comparator import compare_with_internal_docs
from .monitor import fetch_mock_papers

app = FastAPI(title="monitoring-service", version="0.1.0")

PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://localhost:18084")
REPORT_DIR = Path("/app/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class MonitoringRequest(BaseModel):
    keyword: str


class CompareRequest(BaseModel):
    paper_id: str
    query_text: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "monitoring-service"}


@app.post("/monitor/run")
def run_monitoring(payload: MonitoringRequest) -> dict:
    papers = fetch_mock_papers(payload.keyword)

    for paper in papers:
        requests.post(
            f"{PDF_SERVICE_URL}/ingest/paper",
            json={
                "doc_id": paper["paper_id"],
                "title": paper["title"],
                "text": paper["abstract"],
            },
            timeout=10,
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
