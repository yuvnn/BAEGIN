import json
import logging
import os
import sys

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text

import py_eureka_client.eureka_client as eureka_client

from .consumer import start_kafka_consumer, _ARXIV_TO_CATEGORY
from .chroma_client import ensure_collection, get_recent_papers
from .database import engine, Base, get_db
from .models import PaperSummary, PaperRelate

EUREKA_SERVER = os.getenv("EUREKA_SERVER", "http://eureka-server:8761/eureka")
SERVICE_PORT = int(os.getenv("PORT", "8000"))

# Invert mapping: category name → list of arxiv tags
_CATEGORY_TO_ARXIV: Dict[str, List[str]] = {}
for tag, cat in _ARXIV_TO_CATEGORY.items():
    _CATEGORY_TO_ARXIV.setdefault(cat, []).append(tag)

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

    # Online migration: add AIRA Score columns if not present (idempotent)
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE paper_summary "
                "ADD COLUMN IF NOT EXISTS aira_score FLOAT DEFAULT NULL"
            ))
            conn.execute(text(
                "ALTER TABLE paper_summary "
                "ADD COLUMN IF NOT EXISTS aira_decision VARCHAR(50) DEFAULT NULL"
            ))
            conn.commit()
        logger.info("AIRA Score columns ensured in paper_summary.")
    except Exception as e:
        logger.warning(f"Migration warning (non-fatal): {e}")

    # Initialize ChromaDB connection on startup
    try:
        ensure_collection()
        logger.info("ChromaDB collection initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}")

    # Start background Kafka consumer
    logger.info("Starting background Kafka consumer thread...")
    start_kafka_consumer()

    # Register with Eureka
    try:
        await eureka_client.init_async(
            eureka_server=EUREKA_SERVER,
            app_name="paper-service",
            instance_port=SERVICE_PORT,
        )
        logger.info("Registered with Eureka.")
    except Exception as e:
        logger.warning(f"Eureka registration failed (non-fatal): {e}")

    yield
    logger.info("Shutting down paper-service...")
    try:
        await eureka_client.stop_async()
    except Exception:
        pass

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
def list_papers(
    limit: int = 50,
    x_user_keywords: Optional[str] = Header(None),
) -> List[Dict[str, Any]]:
    """
    Returns recently evaluated and summarized papers for the Frontend Dashboard.
    Filters by user keywords (comma-separated arXiv category tags) if provided.
    """
    papers = get_recent_papers(limit)

    # Build allowed category set from X-User-Keywords header
    allowed_categories: Optional[set] = None
    if x_user_keywords and x_user_keywords.strip():
        tags = [t.strip() for t in x_user_keywords.split(",") if t.strip()]
        allowed_categories = set()
        for tag in tags:
            # tag may be an arXiv code (cs.CL) or a display name (Language & Text)
            if tag in _ARXIV_TO_CATEGORY:
                allowed_categories.add(_ARXIV_TO_CATEGORY[tag])
            else:
                # treat as display category name directly
                allowed_categories.add(tag)

    response = []
    for paper in papers:
        try:
            summary_dict = json.loads(paper.get("document", "{}"))
        except Exception:
            summary_dict = {"summary": paper.get("document")}

        metadata = paper.get("metadata", {})
        if allowed_categories is not None:
            paper_cat = metadata.get("category", "")
            if paper_cat not in allowed_categories:
                continue

        response.append({
            "paper_id": paper.get("paper_id"),
            "metadata": metadata,
            "summary_data": summary_dict,
            "aira_score": metadata.get("evaluation_score"),    # stored in ChromaDB
            "aira_decision": metadata.get("evaluation_decision"),
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
        "aira_score": paper.aira_score,
        "aira_decision": paper.aira_decision,
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
