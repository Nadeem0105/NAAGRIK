from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.dependencies import get_current_user_optional, get_district_ids_for_state
from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentResponse
from app.repositories.department_repo import department_repo

router = APIRouter(tags=["Departments"])


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve civic departments, filtered by admin scope if authenticated."""
    # If no user is logged in, or the user is a citizen, return all departments
    if not current_user or current_user.role != "admin":
        return await department_repo.get_all(db)

    scope = current_user.admin_scope

    # Super-admin (or legacy flat admin) sees all
    if scope is None or scope == "super":
        return await department_repo.get_all(db)

    if scope == "district":
        # District admin: only see departments in their district or global/shared (None)
        stmt = select(Department).where(
            or_(
                Department.region_id == current_user.region_id,
                Department.region_id == None
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    if scope == "state":
        # State admin: see departments in their state, districts under their state, or global/shared
        district_ids = await get_district_ids_for_state(current_user.region_id, db)
        allowed_region_ids = district_ids + [current_user.region_id]
        stmt = select(Department).where(
            or_(
                Department.region_id.in_(allowed_region_ids),
                Department.region_id == None
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    return await department_repo.get_all(db)

