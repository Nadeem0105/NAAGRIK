import uuid
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, safe_transaction
from app.repositories.issue_repo import issue_repo
from app.repositories.user_repo import user_repo
from app.services.upload_service import upload_image, upload_video
from app.services.geo_service import reverse_geocode, reverse_geocode_region
from app.services.gamification_service import gamification_service
from app.services.notification_service import notification_service
from app.services.ai_service import run_ai_pipeline
from app.core.exceptions import IssueNotFoundException, UnauthorizedActionException, DuplicateIssueException
from app.core.redis import cache
from sqlalchemy import func

logger = logging.getLogger(__name__)


async def run_ai_pipeline_background(issue_id: uuid.UUID):
    """Background task orchestrator using a fresh DB session."""
    async with AsyncSessionLocal() as session:
        try:
            await run_ai_pipeline(issue_id, session)
        except Exception as e:
            logger.error(f"Background AI pipeline failed for issue {issue_id}: {e}")


class IssueService:
    async def create_issue(
        self,
        reporter_id: uuid.UUID,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        category_hint: Optional[str],
        image_files: list[UploadFile],
        video_file: Optional[UploadFile],
        bg_tasks: BackgroundTasks,
        db: AsyncSession
    ):
        # 1. File Uploads (Images and Video)
        image_urls = []
        image_hashes = []
        for img in image_files:
            url, img_hash = await upload_image(img)
            image_urls.append(url)
            image_hashes.append(img_hash)

        video_url = None
        if video_file:
            video_url, _ = await upload_video(video_file)

        # 2. Reverse Geocoding (address string + region resolution)
        address = await reverse_geocode(latitude, longitude)
        _, district_region = await reverse_geocode_region(latitude, longitude, db)

        # 3. Transaction Block
        async with safe_transaction(db):
            # Create Issue
            issue_data = {
                "reporter_id": reporter_id,
                "title": title,
                "description": description,
                "category": category_hint or "other",
                "severity": "medium",
                "status": "reported",
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "image_urls": image_urls,
                "image_hashes": image_hashes,
                "video_url": video_url,
                "region_id": district_region.id if district_region else None,
            }
            issue = await issue_repo.create(db, issue_data)

            # Create Initial Status History
            history_data = {
                "issue_id": issue.id,
                "status": "reported",
                "note": "Issue reported by citizen.",
                "changed_by": reporter_id,
            }
            await issue_repo.add_status_history(db, history_data)

            # Award points for reporting
            await gamification_service.award_points(db, reporter_id, 10, bg_tasks)

            # Invalidate Caches
            await cache.delete_pattern("map:clusters:*")
            await cache.delete("dashboard:stats")

        # 4. Background Task: AI Processing (runs in separate session)
        bg_tasks.add_task(run_ai_pipeline_background, issue.id)

        return issue

    async def verify_issue(
        self,
        user_id: uuid.UUID,
        issue_id: uuid.UUID,
        verification_type: str,
        bg_tasks: BackgroundTasks,
        db: AsyncSession
    ):
        # Validate verification type
        if verification_type not in ["upvote", "duplicate_flag", "spam_flag", "verify"]:
            raise ValueError(f"Invalid verification type: {verification_type}")

        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise IssueNotFoundException("Issue not found.")

        # Check if already verified by same user for same type
        existing = await issue_repo.get_verification_by_user(db, issue_id, user_id, verification_type)
        if existing:
            raise DuplicateIssueException(f"You have already submitted an {verification_type} for this issue.")

        async with safe_transaction(db):
            # Create verification
            verification_data = {
                "issue_id": issue_id,
                "user_id": user_id,
                "type": verification_type
            }
            await issue_repo.add_verification(db, verification_data)

            # Points distribution logic
            # +1 to voter
            await gamification_service.award_points(db, user_id, 1, bg_tasks)

            if verification_type == "upvote" and issue.reporter_id:
                # +2 to reporter
                await gamification_service.award_points(db, issue.reporter_id, 2, bg_tasks)

            # Auto-verification threshold promotion:
            # If issue gets >= 3 upvotes, move status to "verified" (if currently "reported")
            counts = await issue_repo.get_verifications_count(db, issue_id)
            if verification_type == "upvote" and issue.status == "reported" and counts["upvote"] >= 2: # + the current one makes it 3
                issue.status = "verified"
                # Add status history
                history_data = {
                    "issue_id": issue.id,
                    "status": "verified",
                    "note": "Issue promoted to verified based on community upvotes.",
                    "changed_by": user_id,
                }
                await issue_repo.add_status_history(db, history_data)
                
                # Invalidate cache
                await cache.delete("dashboard:stats")
                await cache.delete_pattern("map:clusters:*")

        return {"status": "success", "message": "Verification submitted successfully."}

    async def add_comment(
        self,
        user_id: uuid.UUID,
        issue_id: uuid.UUID,
        text: str,
        bg_tasks: BackgroundTasks,
        db: AsyncSession
    ):
        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise IssueNotFoundException("Issue not found.")

        async with safe_transaction(db):
            comment_data = {
                "issue_id": issue_id,
                "user_id": user_id,
                "comment": text
            }
            comment = await issue_repo.add_comment(db, comment_data)

            # Award +1 point for commenting
            await gamification_service.award_points(db, user_id, 1, bg_tasks)

        return comment

    async def update_issue_status(
        self,
        admin_id: uuid.UUID,
        issue_id: uuid.UUID,
        status: str,
        notes: Optional[str],
        bg_tasks: BackgroundTasks,
        db: AsyncSession
    ):
        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise IssueNotFoundException("Issue not found.")

        old_status = issue.status
        if old_status == status:
            return issue

        async with safe_transaction(db):
            issue.status = status
            if status == "resolved":
                import datetime
                issue.resolved_at = datetime.datetime.utcnow()

            # Record history
            history_data = {
                "issue_id": issue_id,
                "status": status,
                "note": notes or f"Status updated from {old_status} to {status}.",
                "changed_by": admin_id,
            }
            await issue_repo.add_status_history(db, history_data)

            # Gamification points for resolution
            if status == "resolved" and issue.reporter_id:
                # +15 to reporter
                await gamification_service.award_points(db, issue.reporter_id, 15, bg_tasks)

            # Invalidate caches
            await cache.delete("dashboard:stats")
            await cache.delete_pattern("map:clusters:*")

        # Send status change notification asynchronously
        bg_tasks.add_task(notification_service.notify_status_change, issue_id, status, notes)

        return issue

    async def assign_issue(
        self,
        admin_id: uuid.UUID,
        issue_id: uuid.UUID,
        department_id: Optional[uuid.UUID],
        assigned_to_user_id: Optional[uuid.UUID],
        notes: Optional[str],
        bg_tasks: BackgroundTasks,
        db: AsyncSession
    ):
        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise IssueNotFoundException("Issue not found.")

        async with safe_transaction(db):
            if department_id:
                issue.assigned_department_id = department_id
                issue.status = "assigned"
            if assigned_to_user_id:
                issue.assigned_to_user_id = assigned_to_user_id
                issue.status = "in_progress"

            history_notes = notes or f"Issue assigned. Dept: {department_id}, User: {assigned_to_user_id}"
            history_data = {
                "issue_id": issue_id,
                "status": issue.status,
                "note": history_notes,
                "changed_by": admin_id,
            }
            await issue_repo.add_status_history(db, history_data)
            
            # Invalidate cache
            await cache.delete("dashboard:stats")
            await cache.delete_pattern("map:clusters:*")

        return issue

    async def admin_update_issue(
        self,
        admin_id: uuid.UUID,
        issue_id: uuid.UUID,
        category: Optional[str],
        severity: Optional[str],
        status: Optional[str],
        assigned_department_id: Optional[uuid.UUID],
        assigned_to_user_id: Optional[uuid.UUID],
        bg_tasks: BackgroundTasks,
        db: AsyncSession,
        resolution_image_url: Optional[str] = None,
        sla_due_at: Optional[datetime] = None
    ):
        issue = await issue_repo.get_by_id(db, issue_id)
        if not issue:
            raise IssueNotFoundException("Issue not found.")

        old_status = issue.status
        status_changed = status and status != old_status

        async with safe_transaction(db):
            if category:
                issue.category = category.lower()
            if severity:
                issue.severity = severity.lower()
            if assigned_department_id:
                issue.assigned_department_id = assigned_department_id
            if assigned_to_user_id:
                issue.assigned_to_user_id = assigned_to_user_id
            if resolution_image_url:
                issue.resolution_image_url = resolution_image_url
            if sla_due_at:
                issue.sla_due_at = sla_due_at.replace(tzinfo=None) if sla_due_at.tzinfo else sla_due_at
            if status:
                issue.status = status
                if status == "resolved":
                    import datetime
                    issue.resolved_at = datetime.datetime.utcnow()

            # If status changed, record history and notify
            if status_changed:
                history_data = {
                    "issue_id": issue_id,
                    "status": status,
                    "note": f"Status updated to '{status}' by admin.",
                    "changed_by": admin_id,
                }
                await issue_repo.add_status_history(db, history_data)

                # Gamification points for resolution
                if status == "resolved" and issue.reporter_id:
                    await gamification_service.award_points(db, issue.reporter_id, 15, bg_tasks)

            # Invalidate caches
            await cache.delete("dashboard:stats")
            await cache.delete_pattern("map:clusters:*")

        if status_changed:
            bg_tasks.add_task(notification_service.notify_status_change, issue_id, status)

        return issue


# Singleton instance
issue_service = IssueService()

