import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import py_eureka_client.eureka_client as eureka_client

# ── DB ──────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserRow(Base):
    __tablename__ = "users"
    user_id  = Column(String(255), primary_key=True)
    email    = Column(String(255), unique=True, nullable=False, index=True)
    name     = Column(String(255), nullable=False)
    keywords = Column(Text, nullable=True)   # JSON array string
    team     = Column(String(255), nullable=True)


# ── Pydantic ─────────────────────────────────────────────────────────────────
class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    keywords: List[str] = []
    team: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    name: str
    keywords: List[str] = []


# ── Helpers ──────────────────────────────────────────────────────────────────
import json

def _row_to_dict(row: UserRow) -> dict:
    kws = []
    try:
        kws = json.loads(row.keywords or "[]")
    except Exception:
        pass
    return {
        "user_id": row.user_id,
        "email": row.email,
        "name": row.name,
        "keywords": kws,
        "team": row.team,
    }


EUREKA_SERVER = os.getenv("EUREKA_SERVER", "http://eureka-server:8761/eureka")
SERVICE_PORT  = int(os.getenv("PORT", "8000"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        await eureka_client.init_async(
            eureka_server=EUREKA_SERVER,
            app_name="user-service",
            instance_port=SERVICE_PORT,
        )
    except Exception as e:
        print(f"Eureka registration failed (non-fatal): {e}")
    yield
    try:
        await eureka_client.stop_async()
    except Exception:
        pass


app = FastAPI(title="user-service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "user-service"}


@app.post("/users/register")
def register_user(req: RegisterRequest) -> dict:
    db = SessionLocal()
    try:
        row = db.query(UserRow).filter_by(email=req.email).first()
        if row:
            row.name = req.name
            row.keywords = json.dumps(req.keywords, ensure_ascii=False)
            db.commit()
            db.refresh(row)
        else:
            row = UserRow(
                user_id=req.email,
                email=req.email,
                name=req.name,
                keywords=json.dumps(req.keywords, ensure_ascii=False),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
        return _row_to_dict(row)
    finally:
        db.close()


@app.get("/users/me")
def get_me(x_user_email: Optional[str] = Header(None)) -> dict:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    db = SessionLocal()
    try:
        row = db.query(UserRow).filter_by(email=x_user_email).first()
        if not row:
            return {"email": x_user_email, "name": x_user_email.split("@")[0], "keywords": []}
        return _row_to_dict(row)
    finally:
        db.close()


@app.post("/users")
def upsert_user(profile: UserProfile) -> dict:
    db = SessionLocal()
    try:
        row = db.query(UserRow).filter_by(user_id=profile.user_id).first()
        if row:
            row.email    = profile.email
            row.name     = profile.name
            row.keywords = json.dumps(profile.keywords, ensure_ascii=False)
            row.team     = profile.team
        else:
            row = UserRow(
                user_id=profile.user_id,
                email=profile.email,
                name=profile.name,
                keywords=json.dumps(profile.keywords, ensure_ascii=False),
                team=profile.team,
            )
            db.add(row)
        db.commit()
        db.refresh(row)
        return _row_to_dict(row)
    finally:
        db.close()


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.query(UserRow).filter_by(user_id=user_id).first()
        if not row:
            return {"error": "not_found"}
        return _row_to_dict(row)
    finally:
        db.close()
