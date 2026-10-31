from datetime import UTC, timedelta

import bcrypt
import jwt

from app.core.config import settings


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def make_token(user_id: str, kind: str) -> str:
    ttl = timedelta(minutes=settings.access_minutes) if kind == "access" else timedelta(days=settings.refresh_days)
    # JWT validity uses real time; simulated clock must not expire sessions.
    from datetime import datetime

    n = datetime.now(UTC)
    return jwt.encode({"sub": user_id, "typ": kind, "iat": n, "exp": n + ttl}, settings.jwt_secret, "HS256")


def decode_token(token: str, kind: str) -> str:
    data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if data.get("typ") != kind:
        raise jwt.InvalidTokenError("wrong token type")
    return data["sub"]
