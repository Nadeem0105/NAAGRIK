import logging
import uuid
import resend
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.models.issue import Issue
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Configure Resend if key is available
RESEND_CONFIGURED = False
if settings.RESEND_API_KEY and not settings.RESEND_API_KEY.startswith("re_your"):
    try:
        resend.api_key = settings.RESEND_API_KEY
        RESEND_CONFIGURED = True
        logger.info("Resend email service configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Resend API key: {e}")


class NotificationService:
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send an email using Resend, or fallback to logging."""
        if RESEND_CONFIGURED:
            try:
                params = {
                    "from": settings.NOTIFICATION_FROM_EMAIL,
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                }
                # Since resend SDK is synchronous, run in executor to prevent event loop blocking
                import asyncio
                await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Email sent successfully to {to_email}")
                return True
            except Exception as e:
                logger.error(f"Resend failed to send email to {to_email}: {e}")
                return False
        else:
            logger.info("================[ MOCK EMAIL SENT ]================")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content: {html_content[:200]}...")
            logger.info("===================================================")
            return True

    async def create_in_app_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        message: str,
        issue_id: Optional[uuid.UUID] = None
    ) -> Notification:
        """Create an in-app notification in the database."""
        notification = Notification(
            user_id=user_id,
            issue_id=issue_id,
            message=message,
            is_read=False
        )
        db.add(notification)
        await db.flush()
        return notification

    async def notify_status_change(self, issue_id: uuid.UUID, new_status: str, notes: Optional[str] = None) -> None:
        """Fetch issue details and notify the reporter and all followers in-app + email. Runs in a fresh session."""
        async with AsyncSessionLocal() as db:
            async with db.begin():
                # Fetch issue with reporter details
                stmt = select(Issue).where(Issue.id == issue_id)
                res = await db.execute(stmt)
                issue = res.scalar_one_or_none()
                
                if not issue:
                    return

                # Build notification text
                notes_suffix = f" Notes: {notes}" if notes else ""
                message = f"Update: The status of report '{issue.title}' has been changed to '{new_status}'.{notes_suffix}"

                # 1. Notify Reporter
                if issue.reporter_id:
                    stmt_user = select(User).where(User.id == issue.reporter_id)
                    res_user = await db.execute(stmt_user)
                    reporter = res_user.scalar_one_or_none()
                    if reporter:
                        await self.create_in_app_notification(db, reporter.id, message, issue.id)
                        if reporter.email:
                            subject = f"Nagarik - Status Update on your report"
                            html_body = f"""
                            <h3>Hello {reporter.name},</h3>
                            <p>There has been a status change on your reported civic issue: <strong>{issue.title}</strong>.</p>
                            <p>New Status: <strong>{new_status.upper().replace('_', ' ')}</strong></p>
                            {f"<p>Notes: <em>{notes}</em></p>" if notes else ""}
                            <br/>
                            <p>Thank you for contributing to your community!</p>
                            <p><em>- The Nagarik Team</em></p>
                            """
                            await self.send_email(to_email=reporter.email, subject=subject, html_content=html_body)

                # 2. Notify Followers
                from app.models.issue_follower import IssueFollower
                followers_stmt = select(User).join(IssueFollower, IssueFollower.user_id == User.id).where(IssueFollower.issue_id == issue_id)
                followers_res = await db.execute(followers_stmt)
                followers = followers_res.scalars().all()

                for follower in followers:
                    if follower.id == issue.reporter_id:
                        continue # Already notified as reporter
                    
                    await self.create_in_app_notification(db, follower.id, message, issue.id)
                    if follower.email:
                        subject = f"Nagarik - Status Update on followed issue"
                        html_body = f"""
                        <h3>Hello {follower.name},</h3>
                        <p>There has been a status change on a civic issue you are following: <strong>{issue.title}</strong>.</p>
                        <p>New Status: <strong>{new_status.upper().replace('_', ' ')}</strong></p>
                        {f"<p>Notes: <em>{notes}</em></p>" if notes else ""}
                        <br/>
                        <p>Thank you for staying active in your neighborhood!</p>
                        <p><em>- The Nagarik Team</em></p>
                        """
                        await self.send_email(to_email=follower.email, subject=subject, html_content=html_body)


# Singleton instance
notification_service = NotificationService()
