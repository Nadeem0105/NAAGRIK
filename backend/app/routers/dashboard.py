# f:\CN Hackathon\backend\app\routers\dashboard.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.dashboard import ImpactResponse, HotspotResponse, DepartmentPerformance
from app.services.dashboard_service import dashboard_service
from app.services.hotspot_service import hotspot_service

from app.core.dependencies import require_admin, get_current_user_optional
from app.models.user import User

router = APIRouter(tags=["Dashboard & Analytics"], prefix="/dashboard")


async def resolve_admin_region_ids(user: Optional[User], db: AsyncSession) -> Optional[list[uuid.UUID]]:
    if not user or user.role != "admin":
        return None
    
    scope = user.admin_scope
    if scope is None or scope == "super":
        return None
        
    if scope == "district":
        return [user.region_id]
        
    if scope == "state":
        from app.core.dependencies import get_district_ids_for_state
        district_ids = await get_district_ids_for_state(user.region_id, db)
        return district_ids + [user.region_id]
        
    return None


@router.get("/impact", response_model=ImpactResponse)
async def get_impact(
    response: Response,
    region_id: Optional[uuid.UUID] = Query(None, description="Filter stats to a specific district region"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve public impact statistics with optional regional filtering."""
    # Set public cache header for 60 seconds
    response.headers["Cache-Control"] = "public, max-age=60"
    
    region_ids = None
    if current_user and current_user.role == "admin":
        admin_regions = await resolve_admin_region_ids(current_user, db)
        if admin_regions is not None:
            if region_id:
                if region_id not in admin_regions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Requested region is outside your jurisdiction"
                    )
                region_ids = [region_id]
            else:
                region_ids = admin_regions
        else:
            region_ids = [region_id] if region_id else None
    else:
        region_ids = [region_id] if region_id else None
        
    stats = await dashboard_service.get_impact_statistics(db, region_ids=region_ids)
    return stats


@router.get("/hotspots", response_model=List[HotspotResponse])
async def get_dashboard_hotspots(
    category: Optional[str] = Query(None),
    days: int = Query(90, ge=7, le=365),
    region_id: Optional[uuid.UUID] = Query(None, description="Filter hotspots to a specific district region"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Retrieve recurring issue zones (hotspots) detected using DBSCAN clustering."""
    admin_regions = await resolve_admin_region_ids(admin_user, db)
    
    region_ids = None
    if admin_regions is not None:
        if region_id:
            if region_id not in admin_regions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Requested region is outside your jurisdiction"
                )
            region_ids = [region_id]
        else:
            region_ids = admin_regions
    else:
        region_ids = [region_id] if region_id else None
        
    return await hotspot_service.detect_hotspots(db=db, category=category, days=days, region_ids=region_ids)


@router.get("/departments", response_model=List[DepartmentPerformance])
async def get_department_rankings(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """Retrieve ranked municipal departments performance."""
    region_ids = await resolve_admin_region_ids(admin_user, db)
    return await dashboard_service.get_department_performance(db, region_ids=region_ids)

