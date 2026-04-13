from fastapi import FastAPI
from pydantic import BaseModel

from .security import create_access_token

app = FastAPI(title="auth-server", version="0.1.0")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "auth-server"}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict:
    token = create_access_token(payload.username)
    return {"access_token": token, "token_type": "bearer"}
