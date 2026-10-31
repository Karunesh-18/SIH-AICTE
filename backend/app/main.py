from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.api import admin, auth, dashboards, errors, institutions, notifications, obligations
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import alerts


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        with SessionLocal() as db:
            admin.load_clock(db)
    except OperationalError:  # fresh DB before migrations have run
        pass
    scheduler = None
    if settings.scheduler_enabled:
        from apscheduler.schedulers.background import BackgroundScheduler

        def job():
            with SessionLocal() as db:
                alerts.run_cycle(db)

        scheduler = BackgroundScheduler()
        scheduler.add_job(job, "interval", minutes=settings.alert_cycle_minutes)
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Waymark API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins.split(","),
        # dev: Next may pick another port, and 127.0.0.1 is a different origin from localhost
        allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$" if settings.demo_mode else None,
        allow_methods=["*"], allow_headers=["*"],
    )
    errors.install(app)
    v1 = APIRouter(prefix="/api/v1")
    for r in (auth.router, institutions.router, admin.router, obligations.router,
              notifications.router, dashboards.router):
        v1.include_router(r)
    app.include_router(v1)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
