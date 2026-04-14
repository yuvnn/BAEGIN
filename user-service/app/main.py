from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="user-service", version="0.1.0")

USERS = {}


class UserProfile(BaseModel):
    user_id: str
    name: str
    team: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "user-service"}


@app.post("/users")
def upsert_user(profile: UserProfile) -> dict:
    USERS[profile.user_id] = profile.model_dump()
    return USERS[profile.user_id]


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict:
    return USERS.get(user_id, {"error": "not_found"})
