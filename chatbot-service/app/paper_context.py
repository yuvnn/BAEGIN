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
    LLM 컨텍스트로 주입할 수 있도록 title, category, md_summary 앞부분을 반환합니다.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT paper_id, category, paper_url, authors, md_summary "
                    "FROM paper_summary ORDER BY paper_id DESC LIMIT :lim"
                ),
                {"lim": limit},
            ).fetchall()

        papers = []
        for row in rows:
            paper_id, category, paper_url, authors_raw, md_summary = row
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
                "authors": authors[:3],  # 최대 3명
                "summary_excerpt": summary_excerpt,
            })
        return papers
    except Exception as e:
        logger.error(f"Failed to fetch paper context: {e}")
        return []
