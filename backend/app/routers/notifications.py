import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db, safe_transaction
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse

router = APIRouter(tags=["User Notifications"], prefix="/notifications")


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve in-app notifications for the currently logged-in user, ordered by date."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return result.scalars().all()


@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_as_read(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a specific notification as read."""
    async with safe_transaction(db):
        result = await db.execute(
            select(Notification).where(
                Notification.id == id,
                Notification.user_id == current_user.id
            )
        )
        notification = result.scalars().first()
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
            
        notification.is_read = True

    return notification
