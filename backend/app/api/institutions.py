from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import assert_institution_access, get_current_user
from app.db.session import get_db
from app.models import Institution, User
from app.models.enums import Role
from app.schemas.common import InstitutionDetail, InstitutionOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("")
def list_institutions(
    q: str | None = None,
    state: str | None = None,
    region_id: str | None = None,
    type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(Institution)
    if user.role == Role.INSTITUTION:
        stmt = stmt.where(Institution.id == user.institution_id)
    elif user.role in (Role.SCRUTINY_OFFICER, Role.REGIONAL_OFFICER):
        stmt = stmt.where(Institution.region_id == user.region_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Institution.name.ilike(like), Institution.aicte_code.ilike(like)))
    for col, val in (
        (Institution.state, state), (Institution.region_id, region_id), (Institution.type, type)
    ):
        if val:
            stmt = stmt.where(col == val)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.order_by(Institution.aicte_code).offset((page - 1) * page_size).limit(page_size)
    ).unique()
    return {
        "items": [InstitutionOut.model_validate(r) for r in rows],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{inst_id}", response_model=InstitutionDetail)
def get_institution(
    inst_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    inst = db.scalar(
        select(Institution).options(selectinload(Institution.programs)).where(Institution.id == inst_id)
    )
    if not inst:
        raise HTTPException(404, "Institution not found")
    assert_institution_access(user, inst)
    return inst
