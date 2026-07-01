import uuid
from datetime import datetime, timedelta
from typing import Optional, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import math

from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.models.status_history import StatusHistory


class IssueRepository:
    async def get_by_id(self, db: AsyncSession, issue_id: uuid.UUID) -> Optional[Issue]:
        stmt = (
            select(Issue)
            .where(Issue.id == issue_id)
            .options(
                selectinload(Issue.reporter),
                selectinload(Issue.assigned_user),
                selectinload(Issue.assigned_department),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        reporter_id: Optional[uuid.UUID] = None,
        assigned_to_user_id: Optional[uuid.UUID] = None,
        assigned_department_id: Optional[uuid.UUID] = None,
        is_unassigned: Optional[bool] = None,
        bbox: Optional[tuple[float, float, float, float]] = None,  # min_lat, min_lng, max_lat, max_lng
        region_id: Optional[uuid.UUID] = None,
        state_id: Optional[uuid.UUID] = None,
        visible_to_user_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[Issue], int]:
        # Build query
        query = select(Issue)
        count_query = select(func.count()).select_from(Issue)

        filters = []
        if status:
            filters.append(Issue.status == status)
        if category:
            filters.append(Issue.category == category)
        if severity:
            filters.append(Issue.severity == severity)
        if reporter_id:
            filters.append(Issue.reporter_id == reporter_id)
        if assigned_to_user_id:
            filters.append(Issue.assigned_to_user_id == assigned_to_user_id)
        if assigned_department_id:
            filters.append(Issue.assigned_department_id == assigned_department_id)
        if is_unassigned is True:
            filters.append(Issue.assigned_department_id == None)
            
        if bbox:
            min_lat, min_lng, max_lat, max_lng = bbox
            filters.append(Issue.latitude.between(min_lat, max_lat))
            filters.append(Issue.longitude.between(min_lng, max_lng))

        region_filters = []
        if region_id:
            region_filters.append(Issue.region_id == region_id)
        if state_id:
            from app.models.region import Region
            district_subquery = select(Region.id).where(or_(Region.parent_region_id == state_id, Region.id == state_id))
            region_filters.append(Issue.region_id.in_(district_subquery))

        if region_filters:
            if visible_to_user_id:
                filters.append(or_(Issue.reporter_id == visible_to_user_id, *region_filters))
            else:
                filters.append(or_(*region_filters))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Enforce ordering by created_at DESC
        query = query.order_by(desc(Issue.created_at)).offset(offset).limit(limit)
        
        # Eager load relationships to prevent N+1 queries
        query = query.options(
            selectinload(Issue.reporter),
            selectinload(Issue.assigned_user),
            selectinload(Issue.assigned_department),
        )

        issues_result = await db.execute(query)
        count_result = await db.execute(count_query)

        return list(issues_result.scalars().all()), count_result.scalar() or 0

    async def create(self, db: AsyncSession, issue_data: dict) -> Issue:
        issue = Issue(**issue_data)
        db.add(issue)
        await db.flush()
        return issue

    async def update(self, db: AsyncSession, issue_id: uuid.UUID, update_data: dict) -> Optional[Issue]:
        issue = await self.get_by_id(db, issue_id)
        if not issue:
            return None
        for key, value in update_data.items():
            setattr(issue, key, value)
        db.add(issue)
        await db.flush()
        return issue

    async def find_nearby_active(
        self,
        db: AsyncSession,
        lat: float,
        lng: float,
        radius_meters: float,
        category: Optional[str] = None,
        exclude_id: Optional[uuid.UUID] = None
    ) -> list[Issue]:
        # Fast bounding box check (uses index)
        # 1 degree of latitude is approx 111,000 meters
        # 1 degree of longitude is approx 111,000 * cos(latitude) meters
        lat_delta = radius_meters / 111000.0
        cos_lat = math.cos(math.radians(lat))
        lng_delta = radius_meters / (111000.0 * cos_lat) if cos_lat > 0 else 0.0
        
        # Bounding box filters
        bbox_filters = [
            Issue.latitude.between(lat - lat_delta, lat + lat_delta),
            Issue.longitude.between(lng - lng_delta, lng + lng_delta)
        ]
        
        # Exact distance using Haversine formula in SQL
        rad_lat = math.radians(lat)
        rad_lng = math.radians(lng)
        
        # Distance = 6371000 * acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lng2-lng1))
        # We use a CASE expression or least/greatest to clamp the acos argument to [-1, 1] to avoid NaNs due to float rounding.
        acos_arg = (
            func.sin(rad_lat) * func.sin(func.radians(Issue.latitude)) +
            func.cos(rad_lat) * func.cos(func.radians(Issue.latitude)) * 
            func.cos(func.radians(Issue.longitude) - rad_lng)
        )
        # Clamp acos_arg to [-1.0, 1.0]
        clamped_acos_arg = func.greatest(-1.0, func.least(1.0, acos_arg))
        distance_expr = 6371000 * func.acos(clamped_acos_arg)
        
        query = select(Issue).where(
            and_(
                *bbox_filters,
                distance_expr <= radius_meters
            )
        )
        
        if category:
            query = query.where(Issue.category == category)
        if exclude_id:
            query = query.where(Issue.id != exclude_id)
            
        # Only search active/unresolved issues for duplicates (exclude spam/rejected/flagged)
        query = query.where(Issue.status.notin_(["resolved", "rejected", "flagged"]))
        query = query.where(Issue.category != "spam_flag")
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_coordinates_for_clustering(self, db: AsyncSession, days: int = 90, region_ids: Optional[list[uuid.UUID]] = None) -> list[dict]:
        """Fetch active issues in the last X days with float lat/lng."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        filters = [
            Issue.created_at >= cutoff_date,
            Issue.status.notin_(["resolved", "rejected", "flagged"]),
            Issue.category != "spam_flag"
        ]
        if region_ids:
            filters.append(Issue.region_id.in_(region_ids))
            
        stmt = select(
            Issue.id,
            Issue.category,
            Issue.latitude.label("lat"),
            Issue.longitude.label("lng")
        ).where(
            and_(*filters)
        )
        
        result = await db.execute(stmt)
        return [dict(row._mapping) for row in result.all()]


    async def add_verification(self, db: AsyncSession, verification_data: dict) -> Verification:
        verification = Verification(**verification_data)
        db.add(verification)
        await db.flush()
        return verification

    async def get_verification_by_user(
        self, db: AsyncSession, issue_id: uuid.UUID, user_id: uuid.UUID, verification_type: str
    ) -> Optional[Verification]:
        stmt = select(Verification).where(
            and_(
                Verification.issue_id == issue_id,
                Verification.user_id == user_id,
                Verification.type == verification_type
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_verifications_count(self, db: AsyncSession, issue_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(Verification.type, func.count())
            .where(Verification.issue_id == issue_id)
            .group_by(Verification.type)
        )
        res = await db.execute(stmt)
        counts = {"upvote": 0, "duplicate_flag": 0, "spam_flag": 0, "verify": 0}
        for v_type, count in res.all():
            if v_type in counts:
                counts[v_type] = count
        return counts

    async def add_comment(self, db: AsyncSession, comment_data: dict) -> Comment:
        comment = Comment(**comment_data)
        db.add(comment)
        await db.flush()
        return comment

    async def get_comments_paginated(
        self, db: AsyncSession, issue_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[list[Comment], int]:
        stmt = (
            select(Comment)
            .where(Comment.issue_id == issue_id)
            .order_by(desc(Comment.created_at))
            .offset(offset)
            .limit(limit)
            .options(selectinload(Comment.user))
        )
        count_stmt = select(func.count()).select_from(Comment).where(Comment.issue_id == issue_id)
        
        comments_res = await db.execute(stmt)
        count_res = await db.execute(count_stmt)
        
        return list(comments_res.scalars().all()), count_res.scalar() or 0

    async def add_status_history(self, db: AsyncSession, history_data: dict) -> StatusHistory:
        history = StatusHistory(**history_data)
        db.add(history)
        await db.flush()
        return history


# Singleton instance
issue_repo = IssueRepository()
