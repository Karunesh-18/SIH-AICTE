import os

# Must be set before app modules import settings.
os.environ["DATABASE_URL"] = "sqlite:///./test_waymark.db"
os.environ["DEMO_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.core import clock
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.seed.run import seed


@pytest.fixture(autouse=True)
def db_reset():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    clock.set_offset(0)
    clock.set_fixed(None)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def login(client):
    def _login(email: str) -> dict:
        r = client.post("/api/v1/auth/login", json={"email": email, "password": "Demo@1234"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login
