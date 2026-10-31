"""Idempotent seed (fictional data only). `python -m app.seed.run [--reset]`."""
import sys

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from datetime import timedelta

from app.core import clock
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    AuditLog, Bureau, EscalationLadder, Institution, Notification, Obligation, ObligationAlertLog,
    Program, Region, SystemConfig, User,
)
from app.models.enums import Role

REGIONS = [("Northern", "N"), ("Southern", "S"), ("Eastern", "E"), ("Western", "W"), ("Central", "C")]
BUREAUS = [
    ("Regulation Bureau", "RB", "BUREAU"), ("Grievance Cell", "GC", "CELL"),
    ("Approval Bureau", "AB", "BUREAU"), ("Quality Monitoring Cell", "QMC", "CELL"),
]
# code, name, type, state, city, region
INSTITUTIONS = [
    ("FX-1001", "Northfield Institute of Technology", "ENGINEERING", "Punjab", "Ludhiana", "N"),
    ("FX-1002", "Kaveri Valley College of Engineering", "ENGINEERING", "Karnataka", "Mysuru", "S"),
    ("FX-1003", "Brahmaputra School of Management", "MANAGEMENT", "Assam", "Guwahati", "E"),
    ("FX-1004", "Sahyadri Institute of Pharmacy", "PHARMACY", "Maharashtra", "Pune", "W"),
    ("FX-1005", "Thar Desert Polytechnic", "OTHER", "Rajasthan", "Jodhpur", "N"),
    ("FX-1006", "Narmada Technical Campus", "ENGINEERING", "Madhya Pradesh", "Indore", "C"),
    ("FX-1007", "Lakeview Institute of Management", "MANAGEMENT", "Telangana", "Hyderabad", "S"),
    ("FX-1008", "Deccan Plateau Engineering College", "ENGINEERING", "Karnataka", "Belagavi", "S"),
    ("FX-1009", "Vindhya Institute of Technology", "ENGINEERING", "Madhya Pradesh", "Bhopal", "C"),
    ("FX-1010", "Coastal Bay College of Engineering", "ENGINEERING", "Tamil Nadu", "Chennai", "S"),
    ("FX-1011", "Himalayan Foothills Institute", "OTHER", "Uttarakhand", "Dehradun", "N"),
    ("FX-1012", "Gangetic Plains Management Institute", "MANAGEMENT", "Bihar", "Patna", "E"),
    ("FX-1013", "Malabar Pharmacy College", "PHARMACY", "Kerala", "Kozhikode", "S"),
    ("FX-1014", "Aravalli Technical University College", "ENGINEERING", "Gujarat", "Ahmedabad", "W"),
    ("FX-1015", "Eastern Ghats Institute of Technology", "ENGINEERING", "Odisha", "Bhubaneswar", "E"),
]
PW = "Demo@1234"
# email, name, role, institution code, region code, bureau code
USERS = [
    ("inst.kaveri@demo.test", "Kaveri Registrar", Role.INSTITUTION, "FX-1002", None, None),
    ("inst.northfield@demo.test", "Northfield Registrar", Role.INSTITUTION, "FX-1001", None, None),
    ("scrutiny1@demo.test", "Scrutiny Officer South", Role.SCRUTINY_OFFICER, None, "S", None),
    ("scrutiny2@demo.test", "Scrutiny Officer North", Role.SCRUTINY_OFFICER, None, "N", None),
    ("regional.south@demo.test", "Regional Officer South", Role.REGIONAL_OFFICER, None, "S", None),
    ("regional.north@demo.test", "Regional Officer North", Role.REGIONAL_OFFICER, None, "N", None),
    ("bureau.gc@demo.test", "Grievance Cell Officer", Role.BUREAU_OFFICER, None, None, "GC"),
    ("bureau.rb@demo.test", "Regulation Bureau Officer", Role.BUREAU_OFFICER, None, None, "RB"),
    ("admin@demo.test", "Platform Admin", Role.ADMIN, None, None, None),
]
PROGRAMS = [("B.E. Computer Science", "UG", 120), ("B.E. Mechanical", "UG", 60), ("M.Tech VLSI", "PG", 18)]

LONG = [
    ("T-90", -90, ["INSTITUTION"], "expiry_reminder"),
    ("T-60", -60, ["INSTITUTION"], "expiry_reminder"),
    ("T-30", -30, ["INSTITUTION", "SCRUTINY_OFFICER"], "expiry_reminder"),
    ("T0", 0, ["REGIONAL_OFFICER"], "obligation_due"),
    ("T+3", 3, ["REGIONAL_OFFICER"], "obligation_overdue"),
    ("T+10", 10, ["ADMIN"], "obligation_escalated"),
]
SHORT = [
    ("T-2d", -2, ["SCRUTINY_OFFICER"], "expiry_reminder"),
    ("T0", 0, ["REGIONAL_OFFICER"], "obligation_due"),
    ("T+1d", 1, ["ADMIN"], "obligation_escalated"),
]
LADDERS = {
    "DOCUMENT_EXPIRY": LONG, "UNDERTAKING": LONG, "FDR_MATURITY": LONG, "CUSTOM": LONG,
    "EVC_VISIT": SHORT, "STAGE_SLA": SHORT, "COMPLAINT_SLA": SHORT,
}
# type, title, days from now, institution code
DEMO_OBLIGATIONS = [
    ("DOCUMENT_EXPIRY", "Lease deed validity", 80, "FX-1002"),
    ("DOCUMENT_EXPIRY", "Fire NOC validity", 25, "FX-1002"),
    ("DOCUMENT_EXPIRY", "Land use certificate", -12, "FX-1001"),
    ("FDR_MATURITY", "FDR maturity (Rs 5 lakh)", 55, "FX-1001"),
    ("UNDERTAKING", "Faculty recruitment undertaking", 8, "FX-1003"),
    ("DOCUMENT_EXPIRY", "Audited statement", 140, "FX-1004"),
    ("UNDERTAKING", "Lab equipment undertaking", -5, "FX-1005"),
    ("FDR_MATURITY", "FDR maturity (Rs 3 lakh)", 20, "FX-1006"),
    ("DOCUMENT_EXPIRY", "Fire NOC validity", 200, "FX-1007"),
    ("CUSTOM", "Library accreditation follow-up", 40, "FX-1008"),
]


def seed(db: Session) -> None:
    regions = {c: db.scalar(select(Region).where(Region.code == c)) or Region(name=n, code=c)
               for n, c in REGIONS}
    bureaus = {c: db.scalar(select(Bureau).where(Bureau.code == c)) or Bureau(name=n, code=c, kind=k)
               for n, c, k in BUREAUS}
    db.add_all([*regions.values(), *bureaus.values()])
    db.flush()
    insts = {}
    for i, (code, name, typ, state, city, reg) in enumerate(INSTITUTIONS):
        inst = db.scalar(select(Institution).where(Institution.aicte_code == code))
        if not inst:
            inst = Institution(
                aicte_code=code, name=name, type=typ, state=state, city=city,
                region_id=regions[reg].id, contact_email=f"office@{code.lower()}.demo.test",
                established_year=1985 + i * 2,
            )
            inst.programs = [
                Program(name=n, level=lv, approved_intake=t, start_year=2005 + i)
                for n, lv, t in PROGRAMS[: 2 + (i % 2)]
            ]
            db.add(inst)
        insts[code] = inst
    db.flush()
    for email, name, role, ic, rc, bc in USERS:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(
                email=email, full_name=name, role=role.value, password_hash=hash_password(PW),
                institution_id=insts[ic].id if ic else None,
                region_id=regions[rc].id if rc else None,
                bureau_id=bureaus[bc].id if bc else None,
            ))
    db.flush()
    for typ, steps in LADDERS.items():
        key = f"{typ}_DEFAULT"
        if not db.scalar(select(EscalationLadder).where(EscalationLadder.key == key)):
            db.add(EscalationLadder(key=key, obligation_type=typ, steps=[
                {"key": k, "days_offset": d, "notify": n, "template": t} for k, d, n, t in steps]))
    db.flush()
    if not db.scalar(select(Obligation).limit(1)):
        now = clock.now()
        for typ, title, days, ic in DEMO_OBLIGATIONS:
            steps = db.scalar(select(EscalationLadder.steps).where(
                EscalationLadder.key == f"{typ}_DEFAULT"))
            due = now + timedelta(days=days)
            db.add(Obligation(
                institution_id=insts[ic].id, type=typ, title=title, due_at=due,
                ladder_key=f"{typ}_DEFAULT", ladder_snapshot=steps, source="SYSTEM",
                status="OVERDUE" if days < 0 else "DUE_SOON" if days <= 30 else "UPCOMING",
                last_evaluated_at=now,
            ))
    db.commit()


def reset(db: Session) -> None:
    for model in (Notification, ObligationAlertLog, Obligation, EscalationLadder, AuditLog, SystemConfig, User, Program, Institution, Bureau, Region):
        db.execute(delete(model))
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as db:
        if "--reset" in sys.argv:
            reset(db)
        seed(db)
    print("seeded")
