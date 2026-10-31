from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core import clock
from app.core.config import settings
from app.db.session import get_db, uow
from app.models import AuditLog, SystemConfig, User
from app.models.enums import Role
from app.schemas.common import Strict, UserOut
from app.services import alerts, audit

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles(Role.ADMIN)


class ClockIn(Strict):
    advance_days: float | None = None
    reset: bool = False


def _clock_state() -> dict:
    return {"now": clock.now().isoformat(), "offset_seconds": clock.get_offset_seconds()}


def load_clock(db: Session) -> None:
    row = db.get(SystemConfig, "clock_offset_seconds")
    clock.set_offset(row.value if row else 0)


@router.get("/clock")
def get_clock(_: User = Depends(admin_only)):
    return _clock_state()


@router.post("/clock")
def set_clock(body: ClockIn, user: User = Depends(admin_only), db: Session = Depends(get_db)):
    old = clock.get_offset_seconds()
    new = 0 if body.reset else old + (body.advance_days or 0) * 86400
    with uow(db):
        db.merge(SystemConfig(
            key="clock_offset_seconds", value=new, updated_by=user.id, updated_at=clock.now()
        ))
        audit.append(
            db, actor=user, action="CLOCK.SET", entity_type="system_config",
            entity_id="clock_offset_seconds", before={"offset": old}, after={"offset": new},
        )
    clock.set_offset(new)
    return _clock_state()


@router.get("/audit")
def list_audit(
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    for col, val in (
        (AuditLog.entity_type, entity_type), (AuditLog.entity_id, entity_id),
        (AuditLog.actor_id, actor_id),
    ):
        if val:
            stmt = stmt.where(col == val)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size))
    items = [{c.name: getattr(r, c.name) for c in AuditLog.__table__.columns} for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/audit/verify")
def verify_audit(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return audit.verify(db)


@router.post("/dev/tamper-audit")
def tamper_audit(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Demo only: silently rewrites one audit row (deliberately not audited itself)."""
    if not settings.demo_mode:
        raise HTTPException(404, "Not available")
    row = db.scalar(select(AuditLog).order_by(AuditLog.id.desc()).offset(1).limit(1)) or db.scalar(
        select(AuditLog)
    )
    if not row:
        raise HTTPException(409, "Audit log is empty")
    with uow(db):
        row.after = {**(row.after or {}), "tampered": True}
    return {"tampered_id": row.id}


@router.get("/users", response_model=list[UserOut])
def list_users(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.email)).all()


@router.post("/alert-cycle/run")
def run_alert_cycle(user: User = Depends(admin_only), db: Session = Depends(get_db)):
    return alerts.run_cycle(db, actor=user)


@router.get("/alert-cycle/last")
def last_alert_cycle(_: User = Depends(admin_only), db: Session = Depends(get_db)):
    row = db.get(SystemConfig, "alert_cycle_last")
    return row.value if row else None
