import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Institution, User
from app.models.enums import Role

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    if not cred:
        raise HTTPException(401, "Not authenticated")
    try:
        uid = decode_token(cred.credentials, "access")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(401, "Unknown user")
    return user


def require_roles(*roles: Role):
    allowed = {r.value for r in roles}

    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(403, "Role not permitted")
        return user

    return dep


def can_access_institution(user: User, inst: Institution) -> bool:
    """Object-level scope: own institution / own region / bureau (limited) / admin."""
    if user.role == Role.ADMIN:
        return True
    if user.role == Role.INSTITUTION:
        return user.institution_id == inst.id
    if user.role in (Role.SCRUTINY_OFFICER, Role.REGIONAL_OFFICER):
        return user.region_id == inst.region_id
    return user.role == Role.BUREAU_OFFICER  # limited view; fields trimmed by serializer later


def assert_institution_access(user: User, inst: Institution) -> None:
    if not can_access_institution(user, inst):
        raise HTTPException(403, "Not permitted for this institution")
