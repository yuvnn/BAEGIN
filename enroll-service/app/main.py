from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="enroll-service", version="0.1.0")

RULES = []


class EnrollRule(BaseModel):
    rule_id: str
    keyword: str
    source: str = "arxiv"
    internal_doc_ids: list[str] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "enroll-service"}


@app.post("/rules")
def create_rule(rule: EnrollRule) -> dict:
    RULES.append(rule.model_dump())
    return rule.model_dump()


@app.get("/rules")
def list_rules() -> list[dict]:
    return RULES
