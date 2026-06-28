# f:\CN Hackathon\backend\app\core\dependencies.py
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload


from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# Configure OAuth2/Bearer schema
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """FastAPI Dependency to retrieve the authenticated user from the JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject claim",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
        )

    result = await db.execute(
        select(User)
        .options(joinedload(User.region))
        .where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI Dependency to ensure the authenticated user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privileges required",
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI Dependency to ensure the admin has super scope.
    Region boundary mutations (create/rename state or district) require this.
    Treating admins with no admin_scope as super (legacy flat admins).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privileges required",
        )
    if current_user.admin_scope not in ("super", None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Super-admin privileges required",
        )
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """FastAPI Dependency to retrieve user if JWT is present, or return None if not."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        return None
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    result = await db.execute(
        select(User)
        .options(joinedload(User.region))
        .where(User.id == user_id)
    )
    return result.scalars().first()


# ---------------------------------------------------------------------------
# Jurisdictional Scoping — centralized, single import point
# ---------------------------------------------------------------------------

def get_scope_filter(user: User):
    """
    Return a SQLAlchemy WHERE-clause expression for the given admin's jurisdiction.

    This is the ONE authoritative function for scope resolution.
    Every endpoint that filters issues by admin jurisdiction must use this,
    not reimplement the district/state/super branching inline.

    Returns a SQLAlchemy binary expression (can be passed to .where(...)) or None
    (meaning no filter — super admin / unrestricted).

    Usage:
        scope_expr = get_scope_filter(admin_user)
        query = select(Issue)
        if scope_expr is not None:
            query = query.where(scope_expr)
    """
    from app.models.issue import Issue
    from app.models.region import Region

    scope = user.admin_scope

    # Super-admin or legacy flat admin — unrestricted
    if scope is None or scope == "super":
        return None

    if scope == "district":
        return Issue.region_id == user.region_id

    if scope == "state":
        # Single subquery — no separate round-trip to Python
        district_ids_subq = (
            select(Region.id)
            .where(
                Region.parent_region_id == user.region_id,
                Region.type == "district"
            )
            .scalar_subquery()
        )
        return Issue.region_id.in_(district_ids_subq)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Unknown admin scope: {scope}",
    )


async def scoped_issue_filter(query, user: User, db: AsyncSession):
    """
    Thin wrapper around get_scope_filter() for backward-compat with existing call sites.
    Applies the jurisdictional WHERE clause to a query object in-place.
    Citizens should never call this — it raises 403 for non-admin role.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    scope_expr = get_scope_filter(user)
    if scope_expr is not None:
        query = query.where(scope_expr)
    return query


async def assert_admin_can_access_issue(issue, user: User, db: AsyncSession):
    """
    Raise HTTP 403 if the admin's scope does not include the given issue's region.
    This is the single-item guard used on PATCH/assign endpoints.

    Implements the same logic as get_scope_filter but applied to a fetched Issue object.
    """
    from app.models.region import Region

    scope = user.admin_scope

    if scope is None or scope == "super":
        return  # unrestricted

    if scope == "district":
        if issue.region_id != user.region_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Issue is outside your district jurisdiction",
            )
        return

    if scope == "state":
        # Single subquery check
        stmt = select(Region.id).where(
            Region.parent_region_id == user.region_id,
            Region.type == "district",
            Region.id == issue.region_id,
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Issue is outside your state jurisdiction",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Unknown admin scope: {scope}",
    )


def can_assign(actor: User, target_scope: str, target_region_id: Optional[uuid.UUID]) -> bool:
    """
    Cascading delegation authority check.

    - super → can assign anyone to any scope
    - state → can only create district admins within their own state
    - district → no user-management authority at all

    Returns True if the actor is allowed to make the assignment, False otherwise.
    Callers must resolve target_region from DB before calling this.
    """
    actor_scope = actor.admin_scope

    if actor_scope is None or actor_scope == "super":
        return True

    if actor_scope == "state":
        # State admins may only create district admins, not other state/super admins
        if target_scope != "district":
            return False
        # The target district must belong to this state admin's own state
        # NOTE: parent_region_id check is done in the endpoint after fetching the region
        return True  # parent validation is done in assign_admin_region endpoint

    return False  # district admins have no assignment authority


# Legacy alias kept for old import sites
async def get_district_ids_for_state(state_region_id: uuid.UUID, db: AsyncSession):
    """Return all district region IDs whose parent is the given state region."""
    from app.models.region import Region
    stmt = select(Region.id).where(
        Region.parent_region_id == state_region_id,
        Region.type == "district"
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def ensure_not_last_super_admin(target_user: User, db: AsyncSession):
    """Ensure that we do not demote or deactivate the only remaining super admin."""
    if target_user.role == "admin" and (target_user.admin_scope == "super" or target_user.admin_scope is None):
        stmt = select(func.count(User.id)).where(
            User.role == "admin",
            or_(User.admin_scope == "super", User.admin_scope == None),
            User.id != target_user.id
        )
        res = await db.execute(stmt)
        remaining = res.scalar() or 0
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the only remaining super admin."
            )


async def assert_admin_can_touch_department(department_id: uuid.UUID, user: User, db: AsyncSession):
    """Validate that the admin is authorized to assign or manage the given department based on their region."""
    if not department_id:
        return
    from app.repositories.department_repo import department_repo
    dept = await department_repo.get_by_id(db, department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    
    scope = user.admin_scope
    if scope is None or scope == "super":
        return
        
    if scope == "district":
        if dept.region_id is not None and dept.region_id != user.region_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department is outside your district jurisdiction"
            )
            
    elif scope == "state":
        if dept.region_id is None or dept.region_id == user.region_id:
            return
        # Must be a district under the state
        from app.models.region import Region
        stmt = select(Region.id).where(
            Region.parent_region_id == user.region_id,
            Region.type == "district",
            Region.id == dept.region_id
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department is outside your state jurisdiction"
            )

