import os
import json
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://baegin_user:baegin_password@mariadb:3306/baegin_db"
)

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine


def fetch_paper_context(limit: int = 30) -> list[dict]:
    """
    MariaDB paper_summary 테이블에서 논문 목록을 가져옵니다.
    LLM 컨텍스트로 주입할 수 있도록 핵심 필드만 반환합니다.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT paper_id, category, paper_url, authors, "
                    "md_summary, aira_score, aira_decision "
                    "FROM paper_summary ORDER BY aira_score DESC LIMIT :lim"
                ),
                {"lim": limit},
            ).fetchall()

        papers = []
        for row in rows:
            paper_id, category, paper_url, authors_raw, md_summary, aira_score, aira_decision = row
            try:
                authors = json.loads(authors_raw) if authors_raw else []
            except Exception:
                authors = []

            # md_summary 앞 300자만 컨텍스트로 사용 (토큰 절약)
            summary_excerpt = (md_summary or "")[:300].replace("\n", " ")

            papers.append({
                "paper_id": paper_id,
                "category": category,
                "paper_url": paper_url,
                "authors": authors[:3],
                "summary_excerpt": summary_excerpt,
                "aira_score": float(aira_score) if aira_score is not None else None,
                "aira_decision": aira_decision,
            })
        return papers
    except Exception as e:
        logger.error(f"Failed to fetch paper context: {e}")
        return []


def get_paper_stats() -> dict:
    """
    전체 논문 수, 최고/최저 AIRA Score 등 통계를 반환합니다.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT COUNT(*), "
                    "MAX(aira_score), MIN(aira_score), AVG(aira_score), "
                    "SUM(CASE WHEN aira_score >= 6.0 THEN 1 ELSE 0 END) "
                    "FROM paper_summary"
                )
            ).fetchone()

            top_row = conn.execute(
                text(
                    "SELECT paper_id, aira_score, aira_decision "
                    "FROM paper_summary WHERE aira_score IS NOT NULL "
                    "ORDER BY aira_score DESC LIMIT 1"
                )
            ).fetchone()

        total, max_score, min_score, avg_score, accepted = row
        top_paper = None
        if top_row:
            top_paper = {
                "paper_id": top_row[0],
                "aira_score": float(top_row[1]) if top_row[1] else None,
                "aira_decision": top_row[2],
            }

        return {
            "total": int(total) if total else 0,
            "max_score": float(max_score) if max_score else None,
            "min_score": float(min_score) if min_score else None,
            "avg_score": round(float(avg_score), 2) if avg_score else None,
            "accepted_count": int(accepted) if accepted else 0,
            "top_paper": top_paper,
        }
    except Exception as e:
        logger.error(f"Failed to get paper stats: {e}")
        return {"total": 0, "max_score": None, "min_score": None, "avg_score": None,
                "accepted_count": 0, "top_paper": None}
