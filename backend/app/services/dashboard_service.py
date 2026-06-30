import uuid
import logging
import json
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.issue import Issue
from app.core.redis import cache

logger = logging.getLogger(__name__)


class DashboardService:
    async def get_impact_statistics(self, db: AsyncSession, region_ids: Optional[list[uuid.UUID]] = None) -> dict:
        """Fetch overall civic impact stats. Cached in Redis (2m TTL)."""
        region_key = ",".join(sorted([str(r) for r in region_ids])) if region_ids else "global"
        cache_key = f"dashboard:stats:{region_key}"
        
        # Check cache
        cached_data = await cache.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except Exception:
                pass

        # Build base filter for region, explicitly excluding spam/rejected issues
        region_filter = [Issue.status != "rejected"]
        if region_ids:
            region_filter.append(Issue.region_id.in_(region_ids))

        # 1. Total reported
        total_reported = (await db.execute(
            select(func.count(Issue.id)).where(*region_filter)
        )).scalar() or 0

        # 2. Total resolved
        total_resolved = (await db.execute(
            select(func.count(Issue.id)).where(Issue.status == "resolved", *region_filter)
        )).scalar() or 0

        # 3. Average resolution time
        avg_res_time_seconds = 0.0
        res_time_query = select(
            func.avg(
                func.extract("epoch", Issue.resolved_at) - func.extract("epoch", Issue.created_at)
            )
        ).where(Issue.resolved_at != None, *region_filter)
        
        avg_diff = (await db.execute(res_time_query)).scalar()
        if avg_diff is not None:
            avg_res_time_seconds = float(avg_diff)
            
        avg_resolution_time_hours = round(avg_res_time_seconds / 3600.0, 2)

        # 4. Category breakdown
        cat_query = select(Issue.category, func.count(Issue.id)).where(*region_filter).group_by(Issue.category)
        cat_result = await db.execute(cat_query)
        category_breakdown = {row[0]: row[1] for row in cat_result.all()}

        # 5. Status breakdown
        status_query = select(Issue.status, func.count(Issue.id)).where(*region_filter).group_by(Issue.status)
        status_result = await db.execute(status_query)
        status_breakdown = {row[0]: row[1] for row in status_result.all()}

        stats = {
            "total_reported": total_reported,
            "total_resolved": total_resolved,
            "avg_resolution_time_hours": avg_resolution_time_hours,
            "category_breakdown": category_breakdown,
            "status_breakdown": status_breakdown
        }

        # Write to cache (120 seconds TTL)
        await cache.set(cache_key, stats, ex=120)

        return stats

    async def get_department_performance(self, db: AsyncSession, region_ids: Optional[list[uuid.UUID]] = None) -> list[dict]:
        """Fetch ranked performance statistics for all civic departments."""
        from app.models.department import Department
        from sqlalchemy import or_
        
        # 1. Fetch departments
        if region_ids:
            depts_stmt = select(Department).where(
                or_(
                    Department.region_id.in_(region_ids),
                    Department.region_id == None
                )
            )
        else:
            depts_stmt = select(Department)

        depts_result = await db.execute(depts_stmt)
        depts = depts_result.scalars().all()
        
        performance_list = []
        
        for dept in depts:
            # Explicitly exclude rejected/spam issues from performance metrics
            issue_filter = [
                Issue.assigned_department_id == dept.id,
                Issue.status != "rejected"
            ]
            if region_ids:
                issue_filter.append(Issue.region_id.in_(region_ids))

            # Get assigned count
            assigned_stmt = select(func.count(Issue.id)).where(*issue_filter)
            assigned_count = (await db.execute(assigned_stmt)).scalar() or 0
            
            # Get resolved count
            resolved_stmt = select(func.count(Issue.id)).where(
                Issue.status == "resolved",
                *issue_filter
            )
            resolved_count = (await db.execute(resolved_stmt)).scalar() or 0
            
            # Calculate resolution rate
            resolution_rate = 0.0
            if assigned_count > 0:
                resolution_rate = round((resolved_count / assigned_count) * 100.0, 2)
                
            # Average resolution time
            avg_res_time_seconds = 0.0
            res_time_stmt = select(
                func.avg(
                    func.extract("epoch", Issue.resolved_at) - func.extract("epoch", Issue.created_at)
                )
            ).where(
                Issue.resolved_at != None,
                *issue_filter
            )
            avg_diff = (await db.execute(res_time_stmt)).scalar()
            if avg_diff is not None:
                avg_res_time_seconds = float(avg_diff)
                
            avg_resolution_time_hours = round(avg_res_time_seconds / 3600.0, 2)
            
            performance_list.append({
                "name": dept.name,
                "assigned_count": assigned_count,
                "resolved_count": resolved_count,
                "resolution_rate": resolution_rate,
                "avg_resolution_time_hours": avg_resolution_time_hours
            })
            
        # Sort departments by resolution_rate descending, then resolved_count descending
        performance_list.sort(key=lambda x: (x["resolution_rate"], x["resolved_count"]), reverse=True)
        return performance_list


# Singleton instance
dashboard_service = DashboardService()


