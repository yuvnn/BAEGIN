import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

from .consumer import start_kafka_consumer
from .chroma_client import ensure_collection

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
