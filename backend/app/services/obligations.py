"""Obligation use cases. Each runs in one uow with its audit entry."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import clock
from app.db.session import uow
from app.domain.obligations import obligation_status, step_time
from app.models import EscalationLadder, Institution, Obligation, ObligationAlertLog, User
from app.services import audit


def _snap(o: Obligation) -> dict:
    return {"status": o.status, "due_at": o.due_at.isoformat(), "title": o.title}


def refresh_status(o: Obligation, now: datetime) -> None:
    o.status = obligation_status(
        due_at=o.due_at, now=now, fulfilled=o.fulfilled_at is not None,
        waived=o.waived_at is not None, paused=o.paused_at is not None,
    )
    o.last_evaluated_at = now


def get_or_404(db: Session, obl_id: str) -> Obligation:
    o = db.get(Obligation, obl_id)
    if not o:
        raise HTTPException(404, "Obligation not found")
    return o


def create(db: Session, actor: User, *, institution_id: str, type: str, title: str,
           due_at: datetime, description: str | None = None, ladder_key: str | None = None,
           owner_role: str = "INSTITUTION", source: str = "MANUAL", **links) -> Obligation:
    if not db.get(Institution, institution_id):
        raise HTTPException(404, "Institution not found")
    ladder = db.scalar(select(EscalationLadder).where(
        EscalationLadder.key == (ladder_key or f"{type}_DEFAULT")))
    if not ladder:
        raise HTTPException(422, "No escalation ladder for this obligation type")
    o = Obligation(
        institution_id=institution_id, type=type, title=title, description=description,
        due_at=due_at, owner_role=owner_role, ladder_key=ladder.key,
        ladder_snapshot=ladder.steps, source=source, **links,
    )
    refresh_status(o, clock.now())
    with uow(db):
        db.add(o)
        db.flush()
        audit.append(db, actor=actor, action="OBLIGATION.CREATE", entity_type="obligation",
                     entity_id=o.id, after=_snap(o))
    return o


def _closed(o: Obligation) -> None:
    if o.status in ("FULFILLED", "WAIVED"):
        raise HTTPException(409, f"Obligation already {o.status.lower()}")


def fulfil(db: Session, actor: User, o: Obligation, note: str) -> Obligation:
    _closed(o)
    before = _snap(o)
    with uow(db):
        o.fulfilled_at, o.fulfilled_by = clock.now(), actor.id
        refresh_status(o, clock.now())
        audit.append(db, actor=actor, action="OBLIGATION.FULFIL", entity_type="obligation",
                     entity_id=o.id, before=before, after={**_snap(o), "note": note})
    return o


def waive(db: Session, actor: User, o: Obligation, reason: str) -> Obligation:
    _closed(o)
    before = _snap(o)
    with uow(db):
        o.waived_at, o.waived_by, o.waive_reason = clock.now(), actor.id, reason
        refresh_status(o, clock.now())
        audit.append(db, actor=actor, action="OBLIGATION.WAIVE", entity_type="obligation",
                     entity_id=o.id, before=before, after={**_snap(o), "reason": reason})
    return o


def extend(db: Session, actor: User, o: Obligation, new_due_at: datetime, reason: str) -> Obligation:
    _closed(o)
    before, now = _snap(o), clock.now()
    with uow(db):
        o.due_at = new_due_at
        refresh_status(o, now)
        # D-09: keep SENT steps; let SKIPPED steps that are now in the future fire again.
        skipped = db.scalars(select(ObligationAlertLog).where(
            ObligationAlertLog.obligation_id == o.id, ObligationAlertLog.status == "SKIPPED"))
        steps = {s["key"]: s for s in o.ladder_snapshot}
        stale = [a.id for a in skipped
                 if a.step_key in steps and step_time(new_due_at, steps[a.step_key]) > now]
        if stale:
            db.execute(delete(ObligationAlertLog).where(ObligationAlertLog.id.in_(stale)))
        audit.append(db, actor=actor, action="OBLIGATION.EXTEND", entity_type="obligation",
                     entity_id=o.id, before=before, after={**_snap(o), "reason": reason})
    return o
