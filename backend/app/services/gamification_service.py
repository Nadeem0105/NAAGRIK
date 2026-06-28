import logging
import json
import uuid
from typing import List, Optional
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.badge import Badge
from app.models.user_badge import UserBadge
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.core.redis import cache
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


async def run_badge_check_background(user_id: uuid.UUID):
    """Background task to verify badge conditions and award them in a transaction."""
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        async with db.begin():
            await gamification_service.check_and_award_badges(db, user_id)


class GamificationService:
    async def award_points(self, db: AsyncSession, user_id: uuid.UUID, points: int, bg_tasks: BackgroundTasks) -> None:
        """Increment user points in DB and trigger badge check & leaderboard cache invalidation."""
        user = await user_repo.increment_points(db, user_id, points)
        if user:
            # Trigger badge verification background check
            bg_tasks.add_task(run_badge_check_background, user_id)
            # Invalidate monthly leaderboard cache
            await cache.delete("leaderboard:monthly")

    async def check_and_award_badges(self, db: AsyncSession, user_id: uuid.UUID) -> list[str]:
        """Verify criteria and award new badges. Expected to run inside a transaction."""
        # Counts for criteria checking
        reports_cnt = (await db.execute(
            select(func.count(Issue.id)).where(Issue.reporter_id == user_id)
        )).scalar() or 0

        verifications_cnt = (await db.execute(
            select(func.count(Verification.id)).where(Verification.user_id == user_id)
        )).scalar() or 0

        resolved_cnt = (await db.execute(
            select(func.count(Issue.id)).where(
                Issue.reporter_id == user_id,
                Issue.status == "resolved"
            )
        )).scalar() or 0

        # Fetch all badges
        all_badges_result = await db.execute(select(Badge))
        badges = all_badges_result.scalars().all()

        # Fetch user's current badges
        current_badges_result = await db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        )
        earned_badge_ids = set(current_badges_result.scalars().all())

        newly_earned = []

        for badge in badges:
            if badge.id in earned_badge_ids:
                continue

            crit = badge.criteria or {}
            crit_type = crit.get("type")
            threshold = crit.get("threshold", 1)
            earned = False

            if crit_type == "reports_count" and reports_cnt >= threshold:
                earned = True
            elif crit_type == "verifications_count" and verifications_cnt >= threshold:
                earned = True
            elif crit_type == "resolved_reports" and resolved_cnt >= threshold:
                earned = True

            if earned:
                logger.info(f"User {user_id} earned badge: {badge.name}")
                user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                db.add(user_badge)
                newly_earned.append(badge.name)

        return newly_earned

    async def get_leaderboard(self, db: AsyncSession, limit: int = 20, offset: int = 0) -> list[User]:
        """Fetch the top users sorted by points. Uses Redis caching with 5-minute TTL."""
        cache_key = "leaderboard:monthly"
        
        # Read from Redis
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                users_list = json.loads(cached_data)
                # Double-check limit/offset slicing in memory
                return users_list[offset : offset + limit]
            except Exception:
                pass

        # Database query
        stmt = select(User).order_by(desc(User.points)).limit(100)  # cache top 100
        res = await db.execute(stmt)
        users = res.scalars().all()

        # Serialize list of users
        serialized_users = [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "points": u.points,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]

        # Write to cache
        await cache.set(cache_key, serialized_users, ex=300) # 5 minutes TTL

        # Slice for the response
        return serialized_users[offset : offset + limit]


# Singleton instance
gamification_service = GamificationService()
