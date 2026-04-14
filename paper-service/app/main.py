import json
import logging
import sys

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from .consumer import start_kafka_consumer
from .chroma_client import ensure_collection, get_recent_papers
from .database import engine, Base, get_db
from .models import PaperSummary, PaperRelate

RULES = []

class EnrollRule(BaseModel):
    rule_id: str
    keyword: str
    source: str = "arxiv"
    internal_doc_ids: list[str] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting paper-service lifespan...")
    # Initialize MariaDB Tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("MariaDB tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize MariaDB tables: {e}")

    # Initialize ChromaDB connection on startup
    try:
        ensure_collection()
        logger.info("ChromaDB collection initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}")
        
    # Start background Kafka consumer
    logger.info("Starting background Kafka consumer thread...")
    start_kafka_consumer()
    yield
    logger.info("Shutting down paper-service...")

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


@app.get("/papers/stats")
def get_paper_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns category-level statistics for the frontend dashboard.
    """
    rows = (
        db.query(PaperSummary.category, func.count(PaperSummary.paper_id))
        .group_by(PaperSummary.category)
        .all()
    )
    total = sum(count for _, count in rows)
    by_category = [{"category": cat, "count": count} for cat, count in rows]
    return {"total": total, "by_category": by_category}


@app.get("/papers/{paper_id}")
def get_paper(paper_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns full detail of a single paper from MariaDB.
    """
    paper = db.query(PaperSummary).filter(PaperSummary.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")

    try:
        authors = json.loads(paper.authors) if paper.authors else []
    except Exception:
        authors = []

    return {
        "paper_id": paper.paper_id,
        "category": paper.category,
        "paper_url": paper.paper_url,
        "authors": authors,
        "md_summary": paper.md_summary,
    }


@app.get("/papers/{paper_id}/relates")
def get_paper_relates(paper_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns related internal documents for a paper, ordered by rank.
    """
    paper = db.query(PaperSummary).filter(PaperSummary.paper_id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")

    relates = (
        db.query(PaperRelate)
        .filter(PaperRelate.paper_id == paper_id)
        .order_by(PaperRelate.rank)
        .all()
    )

    return {
        "paper_id": paper_id,
        "relates": [
            {
                "internal_doc_id": r.internal_doc_id,
                "rank": r.rank,
                "reason": r.reason,
            }
            for r in relates
        ],
    }
