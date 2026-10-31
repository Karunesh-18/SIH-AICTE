from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import clock
from app.db.session import get_db, uow
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(unread: bool = False, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    # In-app channel only: other channels are delivery records, not an inbox.
    stmt = select(Notification).where(Notification.user_id == user.id, Notification.channel == "IN_APP")
    if unread:
        stmt = stmt.where(Notification.read_at.is_(None))
    rows = db.scalars(stmt.order_by(Notification.created_at.desc()).limit(100)).all()
    unread_count = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.channel == "IN_APP",
        Notification.read_at.is_(None)))
    return {"unread_count": unread_count, "items": [
        {"id": n.id, "subject": n.subject, "body": n.body, "related_type": n.related_type,
         "related_id": n.related_id, "read_at": n.read_at, "created_at": n.created_at}
        for n in rows]}


@router.post("/{nid}/read")
def mark_read(nid: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, nid)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Notification not found")
    with uow(db):
        n.read_at = n.read_at or clock.now()
    return {"id": n.id, "read_at": n.read_at}
