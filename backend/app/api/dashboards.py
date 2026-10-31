from collections import Counter
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.obligations import scope
from app.core import clock
from app.db.session import get_db
from app.models import Institution, Obligation, User
from app.models.enums import Role

router = APIRouter(prefix="/dashboards", tags=["dashboards"])
viewers = require_roles(Role.INSTITUTION, Role.SCRUTINY_OFFICER, Role.REGIONAL_OFFICER,
                        Role.BUREAU_OFFICER, Role.ADMIN)
OPEN = ("UPCOMING", "DUE_SOON", "OVERDUE", "PAUSED")


@router.get("/compliance")
def compliance(user: User = Depends(viewers), db: Session = Depends(get_db)):
    now = clock.now()
    rows = db.execute(scope(select(Obligation, Institution.name), user)).all()
    by_type: dict[str, Counter] = {}
    upcoming = {"30": 0, "60": 0, "90": 0}
    overdue: Counter = Counter()
    for o, inst_name in rows:
        by_type.setdefault(o.type, Counter())[o.status] += 1
        if o.status == "OVERDUE":
            overdue[(o.institution_id, inst_name)] += 1
        if o.status in ("UPCOMING", "DUE_SOON"):
            for horizon in (30, 60, 90):
                if o.due_at <= now + timedelta(days=horizon):
                    upcoming[str(horizon)] += 1
                    break
    return {
        "total": len(rows),
        "open": sum(1 for o, _ in rows if o.status in OPEN),
        "by_type": {t: dict(c) for t, c in by_type.items()},
        "by_status": dict(Counter(o.status for o, _ in rows)),
        "upcoming": upcoming,
        "top_overdue": [{"institution_id": i, "name": n, "overdue": c}
                        for (i, n), c in overdue.most_common(5)],
    }
