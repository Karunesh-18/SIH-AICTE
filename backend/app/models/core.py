from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, UTCDateTime
from app.models.enums import Role, values


class Region(IdMixin, Base):
    __tablename__ = "regions"
    name: Mapped[str] = mapped_column(String(80), unique=True)
    code: Mapped[str] = mapped_column(String(4), unique=True)


class Bureau(IdMixin, Base):
    __tablename__ = "bureaus"
    __table_args__ = (CheckConstraint("kind IN ('BUREAU','CELL')"),)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    kind: Mapped[str] = mapped_column(String(8), default="BUREAU")


class Institution(IdMixin, Base):
    __tablename__ = "institutions"
    __table_args__ = (
        CheckConstraint("type IN ('ENGINEERING','MANAGEMENT','PHARMACY','OTHER')"),
        CheckConstraint("status IN ('ACTIVE','UNDER_REVIEW')"),
    )
    aicte_code: Mapped[str] = mapped_column(String(16), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(60))
    city: Mapped[str] = mapped_column(String(60))
    region_id: Mapped[str] = mapped_column(ForeignKey("regions.id"), index=True)
    contact_email: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    established_year: Mapped[int] = mapped_column(Integer)
    region: Mapped[Region] = relationship(lazy="joined")
    programs: Mapped[list["Program"]] = relationship(back_populates="institution")


class Program(IdMixin, Base):
    __tablename__ = "programs"
    __table_args__ = (CheckConstraint("level IN ('UG','PG','DIPLOMA')"),)
    institution_id: Mapped[str] = mapped_column(ForeignKey("institutions.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(8))
    approved_intake: Mapped[int] = mapped_column(Integer)
    start_year: Mapped[int] = mapped_column(Integer)
    institution: Mapped[Institution] = relationship(back_populates="programs")


class User(IdMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"role IN ({values(Role)})"),
        CheckConstraint("language IN ('en','hi')"),
    )
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))
    institution_id: Mapped[str | None] = mapped_column(ForeignKey("institutions.id"))
    region_id: Mapped[str | None] = mapped_column(ForeignKey("regions.id"))
    bureau_id: Mapped[str | None] = mapped_column(ForeignKey("bureaus.id"))
    language: Mapped[str] = mapped_column(String(2), default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SystemConfig(Base):
    __tablename__ = "system_config"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict | list | int | float | str | None] = mapped_column(JSON)
    updated_by: Mapped[str | None] = mapped_column(String(36))
    updated_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)
    actor_id: Mapped[str | None] = mapped_column(String(36))
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    before: Mapped[dict | None] = mapped_column(JSON)
    after: Mapped[dict | None] = mapped_column(JSON)
    prev_hash: Mapped[str] = mapped_column(String(64), unique=True)
    hash: Mapped[str] = mapped_column(String(64))


class Outbox(IdMixin, Base):
    """Transactional outbox: notifications written with the state change, dispatched after commit."""

    __tablename__ = "outbox"
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON)
    dispatched_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
