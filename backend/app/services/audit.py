import hashlib
import json
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models import AuditLog

GENESIS = "0" * 64


def _canonical(row: AuditLog) -> str:
    return json.dumps(
        {
            "id": row.id,
            "occurred_at": row.occurred_at.astimezone(UTC).isoformat(),
            "actor_id": row.actor_id,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "before": row.before,
            "after": row.after,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest(prev: str, row: AuditLog) -> str:
    return hashlib.sha256((prev + _canonical(row)).encode()).hexdigest()


def append(db: Session, *, actor, action: str, entity_type: str, entity_id: str,
           before=None, after=None) -> AuditLog:
    """Runs in the caller's transaction. unique(prev_hash) rejects a forked chain on concurrent writers."""
    prev = db.scalar(select(AuditLog.hash).order_by(AuditLog.id.desc()).limit(1)) or GENESIS
    row = AuditLog(
        occurred_at=clock.now(), actor_id=getattr(actor, "id", None),
        actor_role=getattr(actor, "role", None), action=action, entity_type=entity_type,
        entity_id=str(entity_id), before=before, after=after, prev_hash=prev, hash="",
    )
    db.add(row)
    db.flush()  # assigns id, which is part of the hashed payload
    row.hash = _digest(prev, row)
    return row


def verify(db: Session) -> dict:
    prev, count = GENESIS, 0
    for row in db.scalars(select(AuditLog).order_by(AuditLog.id)):
        if row.prev_hash != prev or row.hash != _digest(prev, row):
            return {"ok": False, "count": count, "first_broken_id": row.id}
        prev, count = row.hash, count + 1
    return {"ok": True, "count": count}
