import json
import logging
import os
import sys
import threading

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
from .chroma_client import ensure_collection, get_recent_papers, query_internal_docs
from .database import engine, Base, get_db
from .models import Paper, PaperSummary, PaperRelate

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

    # Online migration (idempotent)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE paper_summary ADD COLUMN IF NOT EXISTS aira_score FLOAT DEFAULT NULL"))
            conn.execute(text("ALTER TABLE paper_summary ADD COLUMN IF NOT EXISTS aira_decision VARCHAR(50) DEFAULT NULL"))
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
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Returns recently evaluated and summarized papers ordered by published_at DESC.
    Filters by user keywords (comma-separated arXiv category tags) if provided.
    """
    # Build allowed category set from X-User-Keywords header
    allowed_categories: Optional[set] = None
    if x_user_keywords and x_user_keywords.strip():
        tags = [t.strip() for t in x_user_keywords.split(",") if t.strip()]
        allowed_categories = set()
        for tag in tags:
            if tag in _ARXIV_TO_CATEGORY:
                allowed_categories.add(_ARXIV_TO_CATEGORY[tag])
            else:
                allowed_categories.add(tag)

    query = (
        db.query(Paper, PaperSummary)
        .join(PaperSummary, Paper.paper_id == PaperSummary.paper_id)
        .order_by(Paper.published_at.is_(None), Paper.published_at.desc())
    )
    if allowed_categories:
        query = query.filter(Paper.category.in_(allowed_categories))

    rows = query.limit(limit).all()

    response = []
    for paper, summary in rows:
        response.append({
            "paper_id": paper.paper_id,
            "metadata": {
                "title": paper.title or "",
                "category": paper.category or "",
                "arxiv_categories": paper.arxiv_categories or "",
                "authors": paper.authors or "[]",
                "published_at": paper.published_at.isoformat() if paper.published_at else None,
                "url": paper.url or "",
                "pdf_url": paper.pdf_url or "",
                "source": paper.source or "",
                "evaluation_score": summary.aira_score,
                "evaluation_decision": summary.aira_decision,
            },
            "summary_data": {"summary": summary.md_summary or ""},
            "aira_score": summary.aira_score,
            "aira_decision": summary.aira_decision,
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
    summary = db.query(PaperSummary).filter(PaperSummary.paper_id == paper_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found")
    paper = db.query(Paper).filter(Paper.paper_id == paper_id).first()

    try:
        authors = json.loads(summary.authors) if summary.authors else []
    except Exception:
        authors = []

    return {
        "paper_id": summary.paper_id,
        "title": paper.title if paper else None,
        "category": summary.category,
        "paper_url": summary.paper_url,
        "authors": authors,
        "abstract": paper.abstract if paper else None,
        "md_summary": summary.md_summary,
        "aira_score": summary.aira_score,
        "aira_decision": summary.aira_decision,
    }


def _compute_relates_for_paper(paper_id: str, md_summary: str, db: Session) -> int:
    """단일 논문에 대해 internal_docs ChromaDB 쿼리 후 PaperRelate 저장. 저장 수 반환."""
    internal_results = query_internal_docs(md_summary, n_results=50)
    if not internal_results or not internal_results.get("ids"):
        return 0

    ids_list = internal_results["ids"][0]
    docs_list = internal_results["documents"][0]
    metas_list = internal_results["metadatas"][0]

    paper_relates: dict[str, dict] = {}
    current_rank = 1
    for i in range(len(ids_list)):
        if current_rank > 10:
            break
        meta = metas_list[i] if metas_list else {}
        chunk_text = docs_list[i]
        internal_doc_id = meta.get("doc_id", "unknown_doc")
        source_file = meta.get("source_file", "Unknown File")
        if internal_doc_id not in paper_relates:
            paper_relates[internal_doc_id] = {
                "internal_doc_id": internal_doc_id,
                "rank": current_rank,
                "reason": f"### 매칭된 내부 문서: {source_file}\n\n- **유사 청크 1**: {chunk_text}\n",
            }
            current_rank += 1
        else:
            paper_relates[internal_doc_id]["reason"] += f"\n- **추가 유사 청크**: {chunk_text}\n"

    for relate_data in paper_relates.values():
        db.merge(PaperRelate(
            paper_id=paper_id,
            internal_doc_id=relate_data["internal_doc_id"],
            rank=relate_data["rank"],
            reason=relate_data["reason"],
        ))
    if paper_relates:
        db.commit()
    return len(paper_relates)


@app.post("/papers/relate/refresh")
def refresh_paper_relates() -> dict:
    """모든 PaperSummary에 대해 internal_docs similarity를 재계산해 PaperRelate를 갱신."""
    def _run():
        _db = next(get_db())
        try:
            summaries = _db.query(PaperSummary).all()
            total = 0
            for s in summaries:
                try:
                    count = _compute_relates_for_paper(s.paper_id, s.md_summary or "", _db)
                    total += count
                except Exception as exc:
                    logger.warning("[relate/refresh] error for %s: %s", s.paper_id, exc)
            logger.info("[relate/refresh] done. total relates=%d", total)
        finally:
            _db.close()

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started", "message": "PaperRelate 재계산이 백그라운드에서 시작됐습니다."}


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
