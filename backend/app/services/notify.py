"""Notification providers (ports and adapters). IN_APP is written inside the use-case transaction;
other channels are QUEUED rows (the outbox) and dispatched after commit."""
import logging
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models import Notification, User

log = logging.getLogger("waymark.notify")

TEMPLATES = {
    "expiry_reminder": ("Reminder: {title}", "{title} for {inst} is due on {due:%d %b %Y}."),
    "obligation_due": ("Due today: {title}", "{title} for {inst} reached its due date."),
    "obligation_overdue": ("Overdue: {title}", "{title} for {inst} is overdue (due {due:%d %b %Y})."),
    "obligation_escalated": (
        "Escalated: {title}", "{title} for {inst} remains overdue since {due:%d %b %Y}."
    ),
}


class Provider(Protocol):
    def send(self, n: Notification, to: User) -> str: ...


class ConsoleEmail:
    def send(self, n, to):  # ponytail: console only; swap in smtplib behind this port
        log.info("EMAIL to=%s subject=%s", to.email, n.subject)
        return "LOGGED"


class StubSms:
    def send(self, n, to):
        log.info("%s stub to=%s subject=%s", n.channel, to.email, n.subject)
        return "LOGGED"


PROVIDERS: dict[str, Provider] = {"EMAIL": ConsoleEmail(), "SMS": StubSms(), "WHATSAPP": StubSms()}


def enqueue(db: Session, users: list[User], *, template: str, ctx: dict, related_type: str,
            related_id: str) -> int:
    subject_t, body_t = TEMPLATES[template]
    subject, body = subject_t.format(**ctx), body_t.format(**ctx)
    for u in users:
        for channel, status in (("IN_APP", "SENT"), ("EMAIL", "QUEUED")):
            db.add(Notification(
                user_id=u.id, channel=channel, subject=subject, body=body, lang=u.language,
                related_type=related_type, related_id=related_id, status=status,
                sent_at=clock.now() if status == "SENT" else None,
            ))
    return len(users)


def dispatch_queued(db: Session) -> int:
    """After commit. A provider failure marks that row FAILED; it never rolls back the use case."""
    rows = db.scalars(select(Notification).where(Notification.status == "QUEUED")).all()
    for n in rows:
        try:
            n.status = PROVIDERS[n.channel].send(n, db.get(User, n.user_id))
            n.sent_at = clock.now()
        except Exception:
            log.exception("dispatch failed for %s", n.id)
            n.status = "FAILED"
    db.commit()
    return len(rows)
