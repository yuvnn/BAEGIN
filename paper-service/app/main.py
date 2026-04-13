import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from .consumer import start_kafka_consumer
from .chroma_client import ensure_collection, get_recent_papers

logger = logging.getLogger(__name__)

RULES = []

class EnrollRule(BaseModel):
    rule_id: str
    keyword: str
    source: str = "arxiv"
    internal_doc_ids: list[str] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize ChromaDB connection on startup
    try:
        ensure_collection()
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}")
        
    # Start background Kafka consumer
    start_kafka_consumer()
    yield
    # Cleanup logic (if any) goes here

app = FastAPI(title="paper-service", version="0.1.0", lifespan=lifespan)

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "paper-service"}

@app.post("/rules")
def create_rule(rule: EnrollRule) -> dict:
    RULES.append(rule.model_dump())
    return rule.model_dump()

@app.get("/rules")
def list_rules() -> list[dict]:
    return RULES

@app.get("/papers")
def list_papers(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Returns recently evaluated and summarized papers for the Frontend Dashboard.
    """
    papers = get_recent_papers(limit)
    response = []
    for paper in papers:
        # Try parsing the summary string back to JSON if possible
        try:
            summary_dict = json.loads(paper.get("document", "{}"))
        except:
            summary_dict = {"summary": paper.get("document")}
            
        response.append({
            "paper_id": paper.get("paper_id"),
            "metadata": paper.get("metadata", {}),
            "summary_data": summary_dict
        })
    return response
