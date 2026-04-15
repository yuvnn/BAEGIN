import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .chatbot_engine import chatbot_engine
from .paper_context import fetch_paper_context, fetch_internal_doc_context, fetch_report_context, get_paper_stats

app = FastAPI(title="chatbot-service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    question: str
    user_keywords: list[str] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "chatbot-service"}


@app.post("/chatbot/recommend")
async def recommend(payload: RecommendRequest) -> dict:
    """
    사용자 질문을 받아 저장된 논문 중 관련 논문을 추천합니다.
    """
    logger.info(f"Chatbot query: {payload.question[:80]}, keywords: {payload.user_keywords}")

    papers = fetch_paper_context(limit=30)
    internal_docs = fetch_internal_doc_context(limit=10)
    reports = fetch_report_context(limit=20)
    stats = get_paper_stats()
    result = await chatbot_engine.recommend(
        payload.question, papers, stats,
        user_keywords=payload.user_keywords,
        internal_docs=internal_docs,
        reports=reports,
    )

    logger.info(
        f"Recommended {len(result.get('recommended_papers', []))} papers"
    )
    return result
