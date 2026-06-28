# f:\CN Hackathon\backend\app\routers\admin.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import (
    require_admin,
    require_super_admin,
    scoped_issue_filter,
    assert_admin_can_access_issue,
    can_assign,
    get_current_user,
    ensure_not_last_super_admin,
    assert_admin_can_touch_department,
)
from app.db.session import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.comment import Comment
from app.models.region import Region
from app.models.department import Department
from app.schemas.issue import IssueResponse, IssueListResponse, IssueUpdateRequest
from app.schemas.region import RegionCreate, RegionUpdate, RegionResponse, RegionTree, AssignRegionRequest
from app.schemas.department import DepartmentResponse, DepartmentCreateRequest, DepartmentUpdateRequest
from app.repositories.issue_repo import issue_repo
from app.repositories.department_repo import department_repo
from app.services.issue_service import issue_service


router = APIRouter(tags=["Admin Operations"], prefix="/admin")


async def build_admin_issue_response(db: AsyncSession, issue: Issue) -> IssueResponse:
    """Helper to populate verification and comment counts on IssueResponse for admin view."""
    # Re-fetch with eager-loaded relationships to prevent async lazy-loading crashes
    fresh_issue = await issue_repo.get_by_id(db, issue.id)
    if fresh_issue:
        issue = fresh_issue

    counts = await issue_repo.get_verifications_count(db, issue.id)

    comment_stmt = select(func.count(Comment.id)).where(Comment.issue_id == issue.id)
    comment_res = await db.execute(comment_stmt)
    comments_count = comment_res.scalar() or 0

    return IssueResponse.from_orm_model(
        issue=issue,
        upvotes=counts["upvote"],
        duplicates=counts["duplicate_flag"],
        spams=counts["spam_flag"],
        comments=comments_count
    )


# ---------------------------------------------------------------------------
# Issue Management — scope-filtered on EVERY endpoint
# ---------------------------------------------------------------------------

@router.get("/issues", response_model=IssueListResponse)
async def admin_list_issues(
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    assigned_department_id: Optional[uuid.UUID] = Query(None),
    assigned_to_user_id: Optional[uuid.UUID] = Query(None),
    is_unassigned: Optional[bool] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None, description="Filter to a specific district region"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """List issues scoped to admin's jurisdiction. Super-admins see everything."""
    offset = (page - 1) * limit

    base_query = select(Issue)

    # ✅ Jurisdictional scope applied on the list view
    base_query = await scoped_issue_filter(base_query, admin_user, db)

    if status_filter:
        base_query = base_query.where(Issue.status == status_filter)
    if category:
        base_query = base_query.where(Issue.category == category)
    if severity:
        base_query = base_query.where(Issue.severity == severity)
    if assigned_to_user_id:
        base_query = base_query.where(Issue.assigned_to_user_id == assigned_to_user_id)
    if assigned_department_id:
        base_query = base_query.where(Issue.assigned_department_id == assigned_department_id)
    if is_unassigned is True:
        base_query = base_query.where(Issue.assigned_department_id == None)  # noqa: E711
    if region_id:
        base_query = base_query.where(Issue.region_id == region_id)

    count_q = select(func.count()).select_from(base_query.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar() or 0

    paginated = (
        base_query
        .order_by(Issue.created_at.desc())
        .offset(offset)
        .limit(limit)
        .options(
            selectinload(Issue.reporter),
            selectinload(Issue.assigned_user),
            selectinload(Issue.assigned_department),
        )
    )
    result = await db.execute(paginated)
    issues = result.scalars().all()

    items = [await build_admin_issue_response(db, issue) for issue in issues]
    return IssueListResponse(items=items, total=total, page=page, limit=limit)


@router.patch("/issues/{id}/assign", response_model=IssueResponse)
async def assign_issue(
    id: uuid.UUID,
    background_tasks: BackgroundTasks,
    assigned_department_id: Optional[uuid.UUID] = Body(None),
    assigned_to_user_id: Optional[uuid.UUID] = Body(None),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Assign an issue to a department or staff member.
    ✅ Jurisdictional scope checked on this single-item endpoint too
    (not just on the list view).
    """
    issue = await issue_repo.get_by_id(db, id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # ✅ Scope guard — district admin from District A cannot reassign District B's issue
    await assert_admin_can_access_issue(issue, admin_user, db)

    # ✅ Department scope guard
    if assigned_department_id:
        await assert_admin_can_touch_department(assigned_department_id, admin_user, db)

    issue = await issue_service.assign_issue(
        admin_id=admin_user.id,
        issue_id=id,
        department_id=assigned_department_id,
        assigned_to_user_id=assigned_to_user_id,
        notes=f"Assigned by administrator {admin_user.name}",
        bg_tasks=background_tasks,
        db=db
    )
    return await build_admin_issue_response(db, issue)


@router.patch("/issues/{id}", response_model=IssueResponse)
async def admin_update_issue(
    id: uuid.UUID,
    payload: IssueUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Update issue details (category, status, severity, assignment).
    ✅ Jurisdictional scope checked on this single-item endpoint too.
    """
    issue = await issue_repo.get_by_id(db, id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # ✅ Scope guard
    await assert_admin_can_access_issue(issue, admin_user, db)

    # ✅ Department scope guard
    if payload.assigned_department_id:
        await assert_admin_can_touch_department(payload.assigned_department_id, admin_user, db)

    issue = await issue_service.admin_update_issue(
        admin_id=admin_user.id,
        issue_id=id,
        category=payload.category,
        severity=payload.severity,
        status=payload.status,
        assigned_department_id=payload.assigned_department_id,
        assigned_to_user_id=payload.assigned_to_user_id,
        bg_tasks=background_tasks,
        db=db,
        resolution_image_url=payload.resolution_image_url,
        sla_due_at=payload.sla_due_at
    )
    return await build_admin_issue_response(db, issue)


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

@router.get("/users")
async def admin_list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_super_admin)  # ✅ Restricted to Super Admin only
):
    """
    List users for admin audit/management.
    - Super-admin: all users.
    - State admin: users scoped to their state or districts within it.
    - District admin: no user listing — 403.
    """
    scope = admin_user.admin_scope

    # District admins have no user-management capability
    if scope == "district":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District admins cannot manage users",
        )

    stmt = select(User).order_by(User.name)
    if scope == "state":
        # Get all districts under this state
        district_ids_subq = (
            select(Region.id)
            .where(
                Region.parent_region_id == admin_user.region_id,
                Region.type == "district"
            )
            .scalar_subquery()
        )
        stmt = stmt.where(
            (User.region_id == admin_user.region_id) |
            (User.region_id.in_(district_ids_subq))
        )

    res = await db.execute(stmt)
    users = res.scalars().all()
    return [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "points": u.points,
        "created_at": u.created_at,
        "admin_scope": u.admin_scope,
        "region_id": u.region_id,
    } for u in users]


@router.get("/users/lookup")
async def lookup_user(
    email: str = Query(..., description="Exact email of the user to look up"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Look up a user by exact email for promotion. Accessible to State and Super Admins."""
    if admin_user.admin_scope == "district":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District admins cannot manage or look up users"
        )
    
    stmt = select(User).where(User.email == email.strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mask email: e.g. john.doe@example.com -> j***e@example.com
    parts = user.email.split("@")
    if len(parts) == 2:
        local, domain = parts
        if len(local) > 2:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        else:
            masked_local = local[0] + "*"
        masked_email = f"{masked_local}@{domain}"
    else:
        masked_email = "***"

    return {
        "id": user.id,
        "name": user.name,
        "email": masked_email,
        "role": user.role,
        "admin_scope": user.admin_scope,
        "region_id": user.region_id
    }



@router.patch("/users/{user_id}/role")
async def admin_update_user_role(
    user_id: uuid.UUID,
    role: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_super_admin)   # ✅ only super-admin can promote/demote roles
):
    """Change a user's role. Super-admin only."""
    if role not in ["citizen", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'citizen' or 'admin'")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Safeguard the last super admin
    await ensure_not_last_super_admin(user, db)

    async with db.begin():
        user.role = role
        db.add(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "points": user.points,
    }


@router.post("/users/{user_id}/assign-region", status_code=200)
async def assign_admin_region(
    user_id: uuid.UUID,
    payload: AssignRegionRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin)    # ← require_admin not require_super_admin — state admins can call this
):
    """
    Assign admin scope + region to a user.
    Implements cascading delegation authority:
      - Super-admin → any scope, any region
      - State admin  → district scope only, within their own state's districts
      - District admin → 403 (no authority)
    """
    if payload.admin_scope not in ("district", "state", "super"):
        raise HTTPException(status_code=400, detail="admin_scope must be 'district', 'state', or 'super'")

    # ✅ Authority check using can_assign()
    if not can_assign(actor, payload.admin_scope, payload.region_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have authority to assign this scope. "
                "State admins can only assign district admins within their own state."
            ),
        )

    # Fetch target user
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate target region exists if provided
    target_region = None
    if payload.region_id:
        region_stmt = select(Region).where(Region.id == payload.region_id)
        region_res = await db.execute(region_stmt)
        target_region = region_res.scalar_one_or_none()
        if not target_region:
            raise HTTPException(status_code=404, detail="Region not found")

    # ✅ State admin parent-region cross-check
    if actor.admin_scope == "state":
        # Double-check: district's parent must be the state admin's own state
        if target_region is None or target_region.parent_region_id != actor.region_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="District is not within your state. You can only assign admins to your own state's districts.",
            )

    # ✅ Safeguard the last super admin before assigning new scope
    await ensure_not_last_super_admin(target_user, db)

    target_user.role = "admin"
    target_user.admin_scope = payload.admin_scope
    target_user.region_id = payload.region_id
    db.add(target_user)
    await db.commit()

    return {
        "id": target_user.id,
        "name": target_user.name,
        "role": target_user.role,
        "admin_scope": target_user.admin_scope,
        "region_id": target_user.region_id,
    }


# ---------------------------------------------------------------------------
# Region Management
# ---------------------------------------------------------------------------

@router.get("/regions", response_model=List[RegionTree])
async def list_regions(
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin)    # ← state admins also allowed, but get scoped view
):
    """
    List regions hierarchically.
    - Super-admin: all states + all districts.
    - State admin: their own state + its districts only.
    - District admin: 403.
    """
    scope = actor.admin_scope

    # District admins have no access to region management
    if scope == "district":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District admins cannot access region management",
        )

    # State admin: scoped to their own state only
    if scope == "state":
        state_stmt = select(Region).where(Region.id == actor.region_id)
        state_res = await db.execute(state_stmt)
        state = state_res.scalar_one_or_none()
        if not state:
            return []

        district_stmt = select(Region).where(
            Region.parent_region_id == state.id,
            Region.type == "district"
        ).order_by(Region.name)
        district_res = await db.execute(district_stmt)
        districts = district_res.scalars().all()

        return [RegionTree(
            id=state.id,
            name=state.name,
            type=state.type,
            parent_region_id=state.parent_region_id,
            children=[RegionResponse.model_validate(d) for d in districts]
        )]

    # Super-admin: all states + districts
    state_stmt = select(Region).where(Region.type == "state").order_by(Region.name)
    state_res = await db.execute(state_stmt)
    states = state_res.scalars().all()

    result = []
    for state in states:
        district_stmt = select(Region).where(
            Region.parent_region_id == state.id,
            Region.type == "district"
        ).order_by(Region.name)
        district_res = await db.execute(district_stmt)
        districts = district_res.scalars().all()

        result.append(RegionTree(
            id=state.id,
            name=state.name,
            type=state.type,
            parent_region_id=state.parent_region_id,
            children=[RegionResponse.model_validate(d) for d in districts]
        ))

    return result


@router.post("/regions", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    payload: RegionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin)   # ✅ Geography mutations stay super-admin only
):
    """Create a new state or district region. Super-admin only."""
    if payload.type not in ("state", "district"):
        raise HTTPException(status_code=400, detail="type must be 'state' or 'district'")

    if payload.type == "district" and not payload.parent_region_id:
        raise HTTPException(status_code=400, detail="Districts must have a parent_region_id (state)")

    if payload.parent_region_id:
        parent_stmt = select(Region).where(Region.id == payload.parent_region_id)
        parent_res = await db.execute(parent_stmt)
        parent = parent_res.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent region not found")

    region = Region(
        id=uuid.uuid4(),
        name=payload.name,
        type=payload.type,
        parent_region_id=payload.parent_region_id
    )
    db.add(region)
    await db.commit()
    await db.refresh(region)
    return region


@router.patch("/regions/{region_id}", response_model=RegionResponse)
async def update_region(
    region_id: uuid.UUID,
    payload: RegionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_super_admin)   # ✅ Geography mutations stay super-admin only
):
    """Rename a region. Super-admin only."""
    stmt = select(Region).where(Region.id == region_id)
    res = await db.execute(stmt)
    region = res.scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    if payload.name:
        region.name = payload.name

    db.add(region)
    await db.commit()
    await db.refresh(region)
    return region


# ---------------------------------------------------------------------------
# Department Management (State/Super Admin only)
# ---------------------------------------------------------------------------

@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_department(
    payload: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Create a new department. State Admin can only create inside their own state."""
    scope = admin_user.admin_scope
    if scope == "district":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District admins cannot manage departments"
        )

    # Check duplicate name
    stmt = select(Department).where(Department.name.ilike(payload.name))
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A department with this name already exists"
        )

    # If state admin, validate region_id is within their state
    if scope == "state":
        if not payload.region_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State admins must associate departments with a region"
            )
        # Check if region is their state or a district under their state
        if payload.region_id != admin_user.region_id:
            stmt = select(Region.id).where(
                Region.parent_region_id == admin_user.region_id,
                Region.type == "district",
                Region.id == payload.region_id
            )
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create departments within your own state"
                )

    new_dept = Department(
        name=payload.name,
        category_mapping=[cat.lower() for cat in payload.category_mapping],
        region_id=payload.region_id
    )
    db.add(new_dept)
    await db.commit()
    await db.refresh(new_dept)
    return new_dept


@router.patch("/departments/{id}", response_model=DepartmentResponse)
async def admin_update_department(
    id: uuid.UUID,
    payload: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Update a department. State Admin can only update inside their own state."""
    scope = admin_user.admin_scope
    if scope == "district":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="District admins cannot manage departments"
        )

    dept = await department_repo.get_by_id(db, id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    # If state admin, validate original department's region
    if scope == "state":
        if dept.region_id != admin_user.region_id:
            stmt = select(Region.id).where(
                Region.parent_region_id == admin_user.region_id,
                Region.type == "district",
                Region.id == dept.region_id
            )
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This department is outside your state jurisdiction"
                )

        # If changing region, validate new region is under their state
        if payload.region_id and payload.region_id != admin_user.region_id:
            stmt = select(Region.id).where(
                Region.parent_region_id == admin_user.region_id,
                Region.type == "district",
                Region.id == payload.region_id
            )
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="New region must be within your own state"
                )

    if payload.name:
        dept.name = payload.name
    if payload.category_mapping is not None:
        dept.category_mapping = [cat.lower() for cat in payload.category_mapping]
    if payload.region_id is not None:
        # If super admin, allow clearing region (setting to None). If state admin, don't allow None.
        if scope == "state" and payload.region_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State admins cannot make departments global"
            )
        dept.region_id = payload.region_id

    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept



# ---------------------------------------------------------------------------
# Proof Upload (any admin, no scope restriction needed for uploads)
# ---------------------------------------------------------------------------

@router.post("/upload-proof")
async def upload_proof(
    file: UploadFile = File(...),
    admin_user: User = Depends(require_admin)
):
    """Upload an image for resolution proof. Returns the secure URL."""
    from app.services.upload_service import upload_image
    url, _ = await upload_image(file)
    return {"url": url}
