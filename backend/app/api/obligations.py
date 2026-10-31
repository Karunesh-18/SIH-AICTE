from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_institution_access, get_current_user, require_roles
from app.core import clock
from app.db.session import get_db
from app.domain.obligations import step_time
from app.models import Institution, Obligation, ObligationAlertLog, User
from app.models.enums import ObligationType, Role
from app.schemas.common import Strict
from app.services import obligations as svc

router = APIRouter(prefix="/obligations", tags=["obligations"])
officers = require_roles(Role.SCRUTINY_OFFICER, Role.REGIONAL_OFFICER, Role.ADMIN)
regional_up = require_roles(Role.REGIONAL_OFFICER, Role.ADMIN)
INSTITUTION_FULFILLABLE = {"DOCUMENT_EXPIRY", "UNDERTAKING", "FDR_MATURITY", "CUSTOM"}


class ObligationIn(Strict):
    institution_id: str
    type: ObligationType
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    due_at: datetime
    ladder_key: str | None = None


class FulfilIn(Strict):
    note: str = Field(default="", max_length=1000)
    evidence_document_id: str | None = None


class WaiveIn(Strict):
    reason: str = Field(min_length=5, max_length=1000)


class ExtendIn(Strict):
    new_due_at: datetime
    reason: str = Field(min_length=5, max_length=1000)


def scope(stmt, user: User):
    """List-level scope; mirrors can_see() for single objects."""
    stmt = stmt.join(Institution, Institution.id == Obligation.institution_id)
    if user.role == Role.INSTITUTION:
        return stmt.where(Obligation.institution_id == user.institution_id)
    if user.role in (Role.SCRUTINY_OFFICER, Role.REGIONAL_OFFICER):
        return stmt.where(Institution.region_id == user.region_id)
    if user.role == Role.BUREAU_OFFICER:
        return stmt.where(Obligation.type == "COMPLAINT_SLA")
    return stmt


def load(db: Session, user: User, obl_id: str) -> Obligation:
    o = svc.get_or_404(db, obl_id)
    if user.role == Role.BUREAU_OFFICER:
        if o.type != "COMPLAINT_SLA":
            raise HTTPException(403, "Not permitted for this obligation")
    else:
        assert_institution_access(user, db.get(Institution, o.institution_id))
    return o


def out(db: Session, o: Obligation, detail: bool = False) -> dict:
    now = clock.now()
    inst = db.get(Institution, o.institution_id)
    logs = db.scalars(select(ObligationAlertLog).where(
        ObligationAlertLog.obligation_id == o.id).order_by(ObligationAlertLog.sent_at)).all()
    logged = {a.step_key for a in logs}
    upcoming = sorted(
        (s for s in o.ladder_snapshot if s["key"] not in logged and step_time(o.due_at, s) >= now),
        key=lambda s: s["days_offset"])
    closed = o.status in ("FULFILLED", "WAIVED")
    res = {
        "id": o.id, "institution": {"id": inst.id, "name": inst.name}, "type": o.type,
        "title": o.title, "description": o.description, "due_at": o.due_at, "status": o.status,
        "days_remaining": None if closed else (o.due_at - now).days, "owner_role": o.owner_role,
        "source": o.source, "waive_reason": o.waive_reason, "version": o.version,
        "next_alert": None if closed or not upcoming else
        {"step": upcoming[0]["key"], "at": step_time(o.due_at, upcoming[0])},
        "alerts_sent": [{"step": a.step_key, "status": a.status, "sent_at": a.sent_at} for a in logs],
    }
    if detail:
        res["ladder"] = o.ladder_snapshot
    return res


@router.get("")
def list_obligations(
    status: str | None = None, type: str | None = None, institution_id: str | None = None,
    region_id: str | None = None, due_before: datetime | None = None, owner_me: bool = False,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    stmt = scope(select(Obligation), user)
    for col, val in ((Obligation.status, status), (Obligation.type, type),
                     (Obligation.institution_id, institution_id), (Institution.region_id, region_id)):
        if val:
            stmt = stmt.where(col == val)
    if due_before:
        stmt = stmt.where(Obligation.due_at <= due_before)
    if owner_me:
        stmt = stmt.where(Obligation.owner_role == user.role)
    rows = db.scalars(stmt.order_by(Obligation.due_at)).all()
    start = (page - 1) * page_size
    return {"items": [out(db, o) for o in rows[start:start + page_size]], "total": len(rows),
            "page": page, "page_size": page_size}


@router.get("/calendar")
def calendar(month: str = Query(pattern=r"^\d{4}-\d{2}$"), user: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    y, m = map(int, month.split("-"))
    if not 1 <= m <= 12:
        raise HTTPException(422, "Invalid month")
    start = datetime(y, m, 1, tzinfo=clock.now().tzinfo)
    end = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=start.tzinfo)
    rows = db.scalars(scope(select(Obligation), user).where(
        Obligation.due_at >= start, Obligation.due_at < end).order_by(Obligation.due_at)).all()
    days: dict[str, list] = {}
    for o in rows:
        days.setdefault(o.due_at.date().isoformat(), []).append(
            {"id": o.id, "title": o.title, "type": o.type, "status": o.status})
    return {"month": month, "days": days}


@router.post("", status_code=201)
def create_obligation(body: ObligationIn, user: User = Depends(officers),
                      db: Session = Depends(get_db)):
    inst = db.get(Institution, body.institution_id)
    if not inst:
        raise HTTPException(404, "Institution not found")
    assert_institution_access(user, inst)
    o = svc.create(db, user, source="MANUAL", **body.model_dump())
    return out(db, o, detail=True)


@router.get("/{obl_id}")
def get_obligation(obl_id: str, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return out(db, load(db, user, obl_id), detail=True)


@router.post("/{obl_id}/fulfil")
def fulfil(obl_id: str, body: FulfilIn, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    o = load(db, user, obl_id)
    if user.role == Role.BUREAU_OFFICER:
        raise HTTPException(403, "Role not permitted")
    if user.role == Role.INSTITUTION and (
            o.type not in INSTITUTION_FULFILLABLE or o.owner_role != Role.INSTITUTION):
        raise HTTPException(403, "Institutions can fulfil only their own document obligations")
    return out(db, svc.fulfil(db, user, o, body.note), detail=True)


@router.post("/{obl_id}/waive")
def waive(obl_id: str, body: WaiveIn, user: User = Depends(regional_up),
          db: Session = Depends(get_db)):
    return out(db, svc.waive(db, user, load(db, user, obl_id), body.reason), detail=True)


@router.post("/{obl_id}/extend")
def extend(obl_id: str, body: ExtendIn, user: User = Depends(regional_up),
           db: Session = Depends(get_db)):
    if body.new_due_at <= clock.now():
        raise HTTPException(422, "New due date must be in the future")
    o = load(db, user, obl_id)
    return out(db, svc.extend(db, user, o, body.new_due_at, body.reason), detail=True)
