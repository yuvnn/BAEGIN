from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60


def create_access_token(subject: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
