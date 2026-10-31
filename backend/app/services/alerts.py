"""Alert cycle: recompute status, walk each obligation's ladder, notify.
Idempotent via the alert-log unique (obligation_id, step_key)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.db.session import uow
from app.domain.obligations import steps_to_fire
from app.models import Institution, Obligation, ObligationAlertLog, SystemConfig, User
from app.services import audit, notify
from app.services.obligations import refresh_status

OPEN = ("UPCOMING", "DUE_SOON", "OVERDUE")


def _recipients(db: Session, inst: Institution, roles: list[str]) -> list[User]:
    users: list[User] = []
    for role in roles:
        stmt = select(User).where(User.role == role, User.is_active.is_(True))
        if role == "INSTITUTION":
            stmt = stmt.where(User.institution_id == inst.id)
        elif role in ("SCRUTINY_OFFICER", "REGIONAL_OFFICER"):
            stmt = stmt.where(User.region_id == inst.region_id)
        users += db.scalars(stmt).all()
    return users


def run_cycle(db: Session, actor=None) -> dict:
    now = clock.now()
    stats = {"evaluated": 0, "fired": 0, "skipped": 0, "notifications": 0, "ran_at": now.isoformat()}
    with uow(db):
        for o in db.scalars(select(Obligation).where(Obligation.status.in_(OPEN))).all():
            stats["evaluated"] += 1
            refresh_status(o, now)
            logged = set(db.scalars(
                select(ObligationAlertLog.step_key).where(ObligationAlertLog.obligation_id == o.id)))
            fire, skipped = steps_to_fire(
                now=now, due_at=o.due_at, ladder=o.ladder_snapshot, logged_keys=logged)
            for s in skipped:
                db.add(ObligationAlertLog(obligation_id=o.id, step_key=s["key"], status="SKIPPED",
                                          sent_at=now, recipients=[]))
                stats["skipped"] += 1
            if not fire:
                continue
            inst = db.get(Institution, o.institution_id)
            users = _recipients(db, inst, fire["notify"])
            stats["notifications"] += notify.enqueue(
                db, users, template=fire["template"],
                ctx={"title": o.title, "inst": inst.name, "due": o.due_at},
                related_type="obligation", related_id=o.id)
            db.add(ObligationAlertLog(obligation_id=o.id, step_key=fire["key"], status="SENT",
                                      sent_at=now, recipients=[u.id for u in users]))
            audit.append(db, actor=actor, action="OBLIGATION.ALERT", entity_type="obligation",
                         entity_id=o.id, after={"step": fire["key"], "recipients": len(users)})
            stats["fired"] += 1
        db.merge(SystemConfig(key="alert_cycle_last", value=stats, updated_at=now))
    notify.dispatch_queued(db)
    return stats
