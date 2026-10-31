from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core import clock
from app.db.session import SessionLocal
from app.models import Institution, User
from app.seed.run import USERS
from app.services import audit

API = "/api/v1"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("email", [u[0] for u in USERS])
def test_every_demo_role_logs_in(client, email):
    r = client.post(f"{API}/auth/login", json={"email": email, "password": "Demo@1234"})
    assert r.status_code == 200 and r.json()["user"]["email"] == email


def test_bad_password_and_unauthenticated(client):
    assert client.post(f"{API}/auth/login", json={"email": "admin@demo.test", "password": "x"}).status_code == 401
    assert client.get(f"{API}/institutions").status_code == 401


def test_login_rate_limit(client):
    for _ in range(10):
        client.post(f"{API}/auth/login", json={"email": "rl@demo.test", "password": "x"})
    assert client.post(f"{API}/auth/login", json={"email": "rl@demo.test", "password": "x"}).status_code == 429


def test_institution_user_sees_only_own(client, login):
    h = login("inst.kaveri@demo.test")
    items = client.get(f"{API}/institutions", headers=h).json()["items"]
    assert [i["aicte_code"] for i in items] == ["FX-1002"]
    with SessionLocal() as db:
        other = db.scalar(select(Institution).where(Institution.aicte_code == "FX-1001")).id
        own = db.scalar(select(Institution).where(Institution.aicte_code == "FX-1002")).id
    assert client.get(f"{API}/institutions/{other}", headers=h).status_code == 403
    assert client.get(f"{API}/institutions/{own}", headers=h).status_code == 200


def test_region_scoping(client, login):
    items = client.get(f"{API}/institutions?page_size=100", headers=login("regional.south@demo.test")).json()["items"]
    assert items and {i["state"] for i in items} <= {"Karnataka", "Telangana", "Tamil Nadu", "Kerala"}
    assert client.get(f"{API}/institutions", headers=login("admin@demo.test")).json()["total"] == 15


def test_admin_endpoints_forbidden_to_others(client, login):
    for email in ("inst.kaveri@demo.test", "regional.south@demo.test", "bureau.gc@demo.test"):
        assert client.post(f"{API}/admin/audit/verify", headers=login(email)).status_code == 403


def test_audit_chain_verify_and_tamper(client, login):
    h = login("admin@demo.test")
    for _ in range(3):
        client.post(f"{API}/admin/clock", headers=h, json={"advance_days": 1})
    assert client.post(f"{API}/admin/audit/verify", headers=h).json() == {"ok": True, "count": 3}
    tampered = client.post(f"{API}/admin/dev/tamper-audit", headers=h).json()["tampered_id"]
    res = client.post(f"{API}/admin/audit/verify", headers=h).json()
    assert res["ok"] is False and res["first_broken_id"] == tampered


def test_audit_append_rolls_back_with_failed_use_case():
    with SessionLocal() as db:
        user = db.scalar(select(User))
        try:
            audit.append(db, actor=user, action="X", entity_type="t", entity_id="1")
            raise RuntimeError("boom")
        except RuntimeError:
            db.rollback()
        assert audit.verify(db) == {"ok": True, "count": 0}


def test_clock_offset(client, login):
    fixed = datetime(2026, 1, 1, tzinfo=UTC)
    clock.set_fixed(fixed)
    assert clock.now() == fixed
    clock.set_fixed(None)
    before = clock.now()
    client.post(f"{API}/admin/clock", headers=login("admin@demo.test"), json={"advance_days": 1})
    assert (clock.now() - before).total_seconds() == pytest.approx(86400, abs=5)


def test_language_update(client, login):
    r = client.patch(f"{API}/auth/me", headers=login("admin@demo.test"), json={"language": "hi"})
    assert r.json()["language"] == "hi"
    assert client.patch(f"{API}/auth/me", headers=login("admin@demo.test"), json={"language": "fr"}).status_code == 422
