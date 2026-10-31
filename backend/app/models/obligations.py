from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, UTCDateTime
from app.models.enums import (
    NotificationChannel,
    ObligationSource,
    ObligationStatus,
    ObligationType,
    values,
)


class EscalationLadder(IdMixin, Base):
    __tablename__ = "escalation_ladders"
    __table_args__ = (CheckConstraint(f"obligation_type IN ({values(ObligationType)})"),)
    key: Mapped[str] = mapped_column(String(60), unique=True)
    obligation_type: Mapped[str] = mapped_column(String(20))
    steps: Mapped[list] = mapped_column(JSON)


class Obligation(IdMixin, Base):
    __tablename__ = "obligations"
    __table_args__ = (
        CheckConstraint(f"type IN ({values(ObligationType)})"),
        CheckConstraint(f"status IN ({values(ObligationStatus)})"),
        CheckConstraint(f"source IN ({values(ObligationSource)})"),
        Index("ix_obl_inst_status", "institution_id", "status"),
        Index("ix_obl_due", "due_at"),
        Index("ix_obl_type_status", "type", "status"),
    )
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"))
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(12), default=ObligationStatus.UPCOMING.value)
    owner_role: Mapped[str] = mapped_column(String(20), default="INSTITUTION")
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    ladder_key: Mapped[str] = mapped_column(String(60))
    ladder_snapshot: Mapped[list] = mapped_column(JSON)  # D-09: ladder copied at creation
    source: Mapped[str] = mapped_column(String(16), default=ObligationSource.MANUAL.value)
    application_id: Mapped[str | None] = mapped_column(String(36))
    complaint_id: Mapped[str | None] = mapped_column(String(36))
    document_id: Mapped[str | None] = mapped_column(String(36))
    fulfilled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    fulfilled_by: Mapped[str | None] = mapped_column(String(36))
    waived_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    waived_by: Mapped[str | None] = mapped_column(String(36))
    waive_reason: Mapped[str | None] = mapped_column(Text)
    paused_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class ObligationAlertLog(IdMixin, Base):
    __tablename__ = "obligation_alert_log"
    __table_args__ = (
        UniqueConstraint("obligation_id", "step_key"),
        CheckConstraint("status IN ('SENT','SKIPPED')"),
    )
    obligation_id: Mapped[str] = mapped_column(ForeignKey("obligations.id"), index=True)
    step_key: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(8), default="SENT")
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime)
    recipients: Mapped[list] = mapped_column(JSON, default=list)


class Notification(IdMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(f"channel IN ({values(NotificationChannel)})"),
        CheckConstraint("status IN ('QUEUED','SENT','FAILED','LOGGED')"),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(10))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    lang: Mapped[str] = mapped_column(String(2), default="en")
    related_type: Mapped[str | None] = mapped_column(String(40))
    related_id: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(8), default="QUEUED")
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
