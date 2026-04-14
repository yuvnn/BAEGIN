import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import py_eureka_client.eureka_client as eureka_client

USERS_BY_EMAIL = {}
USERS_BY_ID = {}

EUREKA_SERVER = os.getenv("EUREKA_SERVER", "http://eureka-server:8761/eureka")
SERVICE_PORT = int(os.getenv("PORT", "8000"))


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


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    existing = USERS_BY_EMAIL.get(req.email)
    if existing:
        existing["name"] = req.name
        existing["keywords"] = req.keywords
        return existing
    profile = {
        "user_id": req.email,
        "email": req.email,
        "name": req.name,
        "keywords": req.keywords,
    }
    USERS_BY_EMAIL[req.email] = profile
    USERS_BY_ID[req.email] = profile
    return profile


@app.get("/users/me")
def get_me(x_user_email: Optional[str] = Header(None)) -> dict:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    user = USERS_BY_EMAIL.get(x_user_email)
    if not user:
        return {"email": x_user_email, "name": x_user_email.split("@")[0], "keywords": []}
    return user


@app.post("/users")
def upsert_user(profile: UserProfile) -> dict:
    data = profile.model_dump()
    USERS_BY_ID[profile.user_id] = data
    USERS_BY_EMAIL[profile.email] = data
    return data


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict:
    return USERS_BY_ID.get(user_id, {"error": "not_found"})
