from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core import clock
from app.db.session import SessionLocal
from app.domain.obligations import obligation_status, steps_to_fire
from app.models import Institution, Notification, Obligation, ObligationAlertLog, User
from app.seed.run import LONG
from app.services import alerts, audit

NOW = datetime(2026, 1, 1, tzinfo=UTC)
LADDER = [{"key": k, "days_offset": d, "notify": n, "template": t} for k, d, n, t in LONG]


def days(n):
    return NOW + timedelta(days=n)


# ---- pure rules -------------------------------------------------------------------------
def test_status_branches():
    kw = {"now": NOW}
    assert obligation_status(due_at=days(5), fulfilled=True, waived=True, **kw) == "FULFILLED"
    assert obligation_status(due_at=days(-5), waived=True, paused=True, **kw) == "WAIVED"
    assert obligation_status(due_at=days(-5), paused=True, **kw) == "PAUSED"
    assert obligation_status(due_at=days(-1), **kw) == "OVERDUE"
    assert obligation_status(due_at=days(30), **kw) == "DUE_SOON"
    assert obligation_status(due_at=days(31), **kw) == "UPCOMING"
    assert obligation_status(due_at=NOW, **kw) == "DUE_SOON"  # exactly due is not yet overdue


def test_ladder_offsets_and_idempotency():
    for off, key in [(-90, "T-90"), (-60, "T-60"), (-30, "T-30"), (0, "T0"), (3, "T+3"), (10, "T+10")]:
        fire, skipped = steps_to_fire(now=days(off), due_at=NOW, ladder=LADDER, logged_keys=set())
        assert fire["key"] == key
    assert steps_to_fire(now=days(-91), due_at=NOW, ladder=LADDER, logged_keys=set()) == (None, [])
    assert steps_to_fire(now=days(-30), due_at=NOW, ladder=LADDER, logged_keys={"T-30"})[0]["key"] == "T-60"


def test_ladder_jump_fires_latest_only():
    fire, skipped = steps_to_fire(now=days(4), due_at=NOW, ladder=LADDER, logged_keys={"T-90"})
    assert fire["key"] == "T+3"
    assert [s["key"] for s in skipped] == ["T-60", "T-30", "T0"]


# ---- API / cycle ------------------------------------------------------------------------
def _kaveri(db):
    inst = db.scalar(select(Institution).where(Institution.aicte_code == "FX-1002"))
    user = db.scalar(select(User).where(User.email == "inst.kaveri@demo.test"))
    return inst, user


def _clear_seed_obligations(db):
    for o in db.scalars(select(Obligation)):
        db.delete(o)
    db.commit()


def _new(client, h, inst_id, due_in_days, title="Test deed"):
    r = client.post("/api/v1/obligations", headers=h, json={
        "institution_id": inst_id, "type": "DOCUMENT_EXPIRY", "title": title,
        "due_at": (clock.now() + timedelta(days=due_in_days)).isoformat()})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _inapp(db, user):
    return db.scalars(select(Notification).where(
        Notification.user_id == user.id, Notification.channel == "IN_APP")).all()


def test_t30_fires_once(client, login):
    with SessionLocal() as db:
        _clear_seed_obligations(db)
        inst, user = _kaveri(db)
        inst_id = inst.id
    h = login("scrutiny1@demo.test")
    _new(client, h, inst_id, 31)
    admin = login("admin@demo.test")
    client.post("/api/v1/admin/clock", headers=admin, json={"advance_days": 1})
    r1 = client.post("/api/v1/admin/alert-cycle/run", headers=admin).json()
    r2 = client.post("/api/v1/admin/alert-cycle/run", headers=admin).json()
    assert r1["fired"] == 1 and r2["fired"] == 0
    with SessionLocal() as db:
        assert len(_inapp(db, _kaveri(db)[1])) == 1
        sent = db.scalars(select(ObligationAlertLog).where(ObligationAlertLog.status == "SENT")).all()
        assert [a.step_key for a in sent] == ["T-30"]
        assert audit.verify(db)["ok"]


def test_overdue_steps_at_simulated_times(client, login):
    with SessionLocal() as db:
        _clear_seed_obligations(db)
        inst_id = _kaveri(db)[0].id
    admin = login("admin@demo.test")
    oid = _new(client, admin, inst_id, 1)
    sent = []
    for advance in (1, 3, 7):  # now = due, due+3d, due+10d
        client.post("/api/v1/admin/clock", headers=admin, json={"advance_days": advance})
        client.post("/api/v1/admin/alert-cycle/run", headers=admin)
        with SessionLocal() as db:
            sent.append(sorted(a.step_key for a in db.scalars(select(ObligationAlertLog).where(
                ObligationAlertLog.obligation_id == oid, ObligationAlertLog.status == "SENT"))))
    assert sent == [["T0"], ["T+3", "T0"], ["T+10", "T+3", "T0"]]


def test_waive_needs_reason_and_role(client, login):
    with SessionLocal() as db:
        inst_id = _kaveri(db)[0].id
    admin = login("admin@demo.test")
    oid = _new(client, admin, inst_id, 10)
    assert client.post(f"/api/v1/obligations/{oid}/waive", headers=admin, json={}).status_code == 422
    assert client.post(f"/api/v1/obligations/{oid}/waive", headers=admin,
                       json={"reason": ""}).status_code == 422
    assert client.post(f"/api/v1/obligations/{oid}/waive", headers=login("scrutiny1@demo.test"),
                       json={"reason": "Court order stay"}).status_code == 403
    r = client.post(f"/api/v1/obligations/{oid}/waive", headers=admin, json={"reason": "Court order stay"})
    assert r.status_code == 200 and r.json()["status"] == "WAIVED"


def test_extend_writes_before_after_audit(client, login):
    with SessionLocal() as db:
        inst_id = _kaveri(db)[0].id
    admin = login("admin@demo.test")
    oid = _new(client, admin, inst_id, 10)
    new_due = (clock.now() + timedelta(days=60)).isoformat()
    r = client.post(f"/api/v1/obligations/{oid}/extend", headers=admin,
                    json={"new_due_at": new_due, "reason": "Renewal in progress"})
    assert r.status_code == 200
    rows = client.get("/api/v1/admin/audit", headers=admin,
                      params={"entity_id": oid}).json()["items"]
    ext = next(x for x in rows if x["action"] == "OBLIGATION.EXTEND")
    assert ext["before"]["due_at"] != ext["after"]["due_at"] and ext["after"]["reason"]
    assert client.post("/api/v1/admin/audit/verify", headers=admin).json()["ok"]


def test_institution_scope(client, login):
    with SessionLocal() as db:
        north = db.scalar(select(Institution).where(Institution.aicte_code == "FX-1001")).id
    admin = login("admin@demo.test")
    oid = _new(client, admin, north, 10)
    kaveri = login("inst.kaveri@demo.test")
    assert client.get(f"/api/v1/obligations/{oid}", headers=kaveri).status_code == 403
    items = client.get("/api/v1/obligations", headers=kaveri).json()["items"]
    assert items and all(i["institution"]["name"].startswith("Kaveri") for i in items)
    # institutions cannot waive or create
    assert client.post(f"/api/v1/obligations/{oid}/waive", headers=kaveri,
                       json={"reason": "please"}).status_code == 403


def test_dashboard_matches_db(client, login):
    admin = login("admin@demo.test")
    d = client.get("/api/v1/dashboards/compliance", headers=admin).json()
    with SessionLocal() as db:
        rows = db.scalars(select(Obligation)).all()
    assert d["total"] == len(rows)
    assert d["by_status"].get("OVERDUE", 0) == sum(o.status == "OVERDUE" for o in rows)
    assert sum(sum(v.values()) for v in d["by_type"].values()) == len(rows)


def test_notifications_inbox_and_read(client, login):
    with SessionLocal() as db:
        _clear_seed_obligations(db)
        inst_id = _kaveri(db)[0].id
    admin = login("admin@demo.test")
    _new(client, admin, inst_id, 20)  # already inside T-30 window
    client.post("/api/v1/admin/alert-cycle/run", headers=admin)
    kaveri = login("inst.kaveri@demo.test")
    inbox = client.get("/api/v1/notifications", headers=kaveri).json()
    assert inbox["unread_count"] == 1
    nid = inbox["items"][0]["id"]
    assert client.post(f"/api/v1/notifications/{nid}/read", headers=kaveri).status_code == 200
    assert client.get("/api/v1/notifications", headers=kaveri).json()["unread_count"] == 0
    assert client.post(f"/api/v1/notifications/{nid}/read",
                       headers=login("inst.northfield@demo.test")).status_code == 404
