import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.user_badge import UserBadge
from app.models.badge import Badge
from app.models.issue import Issue
from app.models.verification import Verification
from app.schemas.gamification import LeaderboardEntry, UserBadgeResponse, LeaderboardResponse, LeaderboardScope, ViewerRank, StateResponse
from app.services.gamification_service import gamification_service
from app.core.dependencies import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Gamification"])


async def get_user_scope(current_user: Optional[User], db: AsyncSession):
    if not current_user:
        return "global", None, None
        
    if current_user.role == "super_admin" or (current_user.role == "admin" and current_user.admin_scope == "super"):
        return "global", None, None
        
    from app.models.region import Region

    # State Admin
    if current_user.role == "admin" and current_user.admin_scope == "state":
        state_id = current_user.region_id
        if not state_id:
            logger.warning(f"State admin {current_user.id} has no region_id assigned.")
            return "state", None, None
            
        res = await db.execute(select(Region).where(Region.id == state_id))
        state_region = res.scalar_one_or_none()
        return "state", state_id, state_region.name if state_region else None
        
    # District Admin
    if current_user.role == "admin" and current_user.admin_scope == "district":
        if not current_user.region_id:
            logger.warning(f"District admin {current_user.id} has no region_id assigned.")
            return "state", None, None
            
        res = await db.execute(select(Region).where(Region.id == current_user.region_id))
        district_region = res.scalar_one_or_none()
        if not district_region or not district_region.parent_region_id:
            logger.warning(f"District admin {current_user.id}'s district has no parent state.")
            return "state", None, None
            
        state_id = district_region.parent_region_id
        res = await db.execute(select(Region).where(Region.id == state_id))
        state_region = res.scalar_one_or_none()
        return "state", state_id, state_region.name if state_region else None

    # Citizen
    if current_user.role == "citizen":
        state_id = current_user.state_id
        if not state_id and current_user.region_id:
            res = await db.execute(select(Region).where(Region.id == current_user.region_id))
            reg = res.scalar_one_or_none()
            if reg and reg.parent_region_id:
                state_id = reg.parent_region_id
                
        if not state_id:
            return "state", None, None
            
        res = await db.execute(select(Region).where(Region.id == state_id))
        state_region = res.scalar_one_or_none()
        return "state", state_id, state_region.name if state_region else None

    return "global", None, None


def get_display_name(name: str, role: str) -> str:
    if role == "citizen":
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0]}."
        return name
    return name


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard_route(
    limit: int = Query(50, ge=1, le=100),
    state_id: uuid.UUID | None = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the scoped leaderboard."""
    scope_type, resolved_state_id, state_name = await get_user_scope(current_user, db)
    
    if current_user and (current_user.role == "super_admin" or (current_user.role == "admin" and current_user.admin_scope == "super")):
        if state_id:
            scope_type = "state"
            resolved_state_id = state_id
            from app.models.region import Region
            res = await db.execute(select(Region).where(Region.id == state_id))
            state_region = res.scalar_one_or_none()
            state_name = state_region.name if state_region else None
        else:
            scope_type = "global"
            resolved_state_id = None
            state_name = None

    if scope_type == "state" and not resolved_state_id:
        return LeaderboardResponse(
            scope=LeaderboardScope(type="state", state_id=None, state_name=None),
            entries=[],
            viewer_rank=None
        )

    issues_reported_sub = (
        select(func.count(Issue.id))
        .where(Issue.reporter_id == User.id)
        .correlate(User)
        .label("issues_reported")
    )

    issues_verified_sub = (
        select(func.count(Verification.id))
        .where(Verification.user_id == User.id)
        .correlate(User)
        .label("issues_verified")
    )

    badge_count_sub = (
        select(func.count(UserBadge.badge_id))
        .where(UserBadge.user_id == User.id)
        .correlate(User)
        .label("badge_count")
    )

    from app.models.region import Region

    stmt = select(
        User,
        issues_reported_sub,
        issues_verified_sub,
        badge_count_sub
    )

    if scope_type == "state" and resolved_state_id:
        stmt = stmt.outerjoin(Region, User.region_id == Region.id).where(
            or_(
                User.state_id == resolved_state_id,
                User.region_id == resolved_state_id,
                Region.parent_region_id == resolved_state_id
            )
        )

    stmt = stmt.order_by(
        desc(User.points),
        desc(issues_reported_sub),
        User.created_at.asc()
    ).limit(limit)

    res = await db.execute(stmt)
    rows = res.all()

    entries = []
    for rank, (u, reports, verified, badges) in enumerate(rows, start=1):
        entries.append(
            LeaderboardEntry(
                rank=rank,
                user_id=u.id,
                display_name=get_display_name(u.name, u.role),
                avatar_url=None,
                civic_points=u.points,
                badge_count=badges,
                issues_reported=reports,
                issues_verified=verified,
                role=u.role
            )
        )

    viewer_rank = None
    if current_user:
        ranked_cte = (
            select(
                User.id.label("user_id"),
                User.points.label("points"),
                func.row_number().over(
                    order_by=[
                        desc(User.points),
                        desc(issues_reported_sub),
                        User.created_at.asc()
                    ]
                ).label("rank")
            )
            .outerjoin(Region, User.region_id == Region.id)
        )
        if scope_type == "state" and resolved_state_id:
            ranked_cte = ranked_cte.where(
                or_(
                    User.state_id == resolved_state_id,
                    User.region_id == resolved_state_id,
                    Region.parent_region_id == resolved_state_id
                )
            )
        
        ranked_cte = ranked_cte.cte("ranked_users")
        
        rank_stmt = select(ranked_cte.c.rank, ranked_cte.c.points).where(ranked_cte.c.user_id == current_user.id)
        rank_res = await db.execute(rank_stmt)
        row = rank_res.first()
        if row:
            viewer_rank = ViewerRank(rank=row.rank, civic_points=row.points)

    return LeaderboardResponse(
        scope=LeaderboardScope(
            type=scope_type,
            state_id=resolved_state_id,
            state_name=state_name
        ),
        entries=entries,
        viewer_rank=viewer_rank
    )


@router.get("/leaderboard/my-rank", response_model=ViewerRank)
async def get_my_rank_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve only the authenticated user's position and points in their scoped leaderboard."""
    scope_type, resolved_state_id, _ = await get_user_scope(current_user, db)
    
    if scope_type == "state" and not resolved_state_id:
        return ViewerRank(rank=None, civic_points=current_user.points)
        
    issues_reported_sub = (
        select(func.count(Issue.id))
        .where(Issue.reporter_id == User.id)
        .correlate(User)
        .label("issues_reported")
    )

    from app.models.region import Region

    ranked_cte = (
        select(
            User.id.label("user_id"),
            User.points.label("points"),
            func.row_number().over(
                order_by=[
                    desc(User.points),
                    desc(issues_reported_sub),
                    User.created_at.asc()
                ]
            ).label("rank")
        )
        .outerjoin(Region, User.region_id == Region.id)
    )
    
    if scope_type == "state" and resolved_state_id:
        ranked_cte = ranked_cte.where(
            or_(
                User.state_id == resolved_state_id,
                User.region_id == resolved_state_id,
                Region.parent_region_id == resolved_state_id
            )
        )
        
    ranked_cte = ranked_cte.cte("ranked_users")
    
    rank_stmt = select(ranked_cte.c.rank, ranked_cte.c.points).where(ranked_cte.c.user_id == current_user.id)
    rank_res = await db.execute(rank_stmt)
    row = rank_res.first()
    if row:
        return ViewerRank(rank=row.rank, civic_points=row.points)
        
    return ViewerRank(rank=None, civic_points=current_user.points)


@router.get("/users/{id}/badges", response_model=List[UserBadgeResponse])
async def get_user_badges(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all badges earned by a user."""
    # Run in a simple transaction/read
    stmt = (
        select(UserBadge)
        .where(UserBadge.user_id == id)
        .order_by(desc(UserBadge.earned_at))
        .options(selectinload(UserBadge.badge))
    )
    result = await db.execute(stmt)
    user_badges = result.scalars().all()
    
    return [
        UserBadgeResponse(
            badge_id=ub.badge.id,
            name=ub.badge.name,
            description=ub.badge.description,
            earned_at=ub.earned_at
        )
        for ub in user_badges if ub.badge
    ]


@router.get("/states", response_model=List[StateResponse])
async def list_states(db: AsyncSession = Depends(get_db)):
    """Retrieve all top-level states."""
    from app.models.region import Region
    res = await db.execute(select(Region).where(Region.parent_region_id == None).order_by(Region.name.asc()))
    return res.scalars().all()
