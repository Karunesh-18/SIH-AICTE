import time
from collections import defaultdict, deque

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import decode_token, make_token, verify_password
from app.db.session import get_db, uow
from app.models import User
from app.schemas.common import Strict, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
# ponytail: in-memory per-process; move to a shared store when running multiple workers
_attempts: dict[str, deque] = defaultdict(deque)


class LoginIn(Strict):
    email: str
    password: str


class RefreshIn(Strict):
    refresh_token: str


class MeIn(Strict):
    language: str = Field(pattern="^(en|hi)$")


def _tokens(user: User) -> dict:
    return {
        "access_token": make_token(user.id, "access"),
        "refresh_token": make_token(user.id, "refresh"),
        "user": UserOut.model_validate(user),
    }


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    key, t = body.email.lower(), time.monotonic()
    q = _attempts[key]
    while q and t - q[0] > 300:
        q.popleft()
    if len(q) >= settings.login_max_attempts:
        raise HTTPException(429, "Too many attempts, try later")
    user = db.scalar(select(User).where(User.email == key))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        q.append(t)
        raise HTTPException(401, "Invalid email or password")
    q.clear()
    return _tokens(user)


@router.post("/refresh")
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    try:
        user = db.get(User, decode_token(body.refresh_token, "refresh"))
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")
    if not user or not user.is_active:
        raise HTTPException(401, "Unknown user")
    return {"access_token": make_token(user.id, "access")}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: MeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    with uow(db):
        user.language = body.language
    return user
