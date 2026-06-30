import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, BackgroundTasks, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from app.core.dependencies import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.verification import Verification
from app.models.comment import Comment
from app.schemas.issue import (
    IssueResponse,
    IssueListResponse,
    CommentResponse,
    CommentCreateRequest,
    VerificationResponse,
    VerificationCreateRequest
)
from app.services.issue_service import issue_service
from app.repositories.issue_repo import issue_repo
from app.main import limiter  # import main rate limiter instance

router = APIRouter(tags=["Issues"])


async def build_issue_response(db: AsyncSession, issue: Issue, current_user: Optional[User] = None) -> IssueResponse:
    """Helper to populate verification and comment counts on IssueResponse."""
    # Re-fetch with eager-loaded relationships to prevent async lazy-loading crashes
    from sqlalchemy.orm import selectinload
    fresh_issue = await issue_repo.get_by_id(db, issue.id)
    if fresh_issue:
        issue = fresh_issue

    counts = await issue_repo.get_verifications_count(db, issue.id)
    
    # Get comment count
    comment_stmt = select(func.count(Comment.id)).where(Comment.issue_id == issue.id)
    comment_res = await db.execute(comment_stmt)
    comments_count = comment_res.scalar() or 0

    is_followed = False
    if current_user:
        from app.models.issue_follower import IssueFollower
        follow_stmt = select(func.count(IssueFollower.issue_id)).where(
            IssueFollower.issue_id == issue.id,
            IssueFollower.user_id == current_user.id
        )
        follow_res = await db.execute(follow_stmt)
        is_followed = (follow_res.scalar() or 0) > 0

    return IssueResponse.from_orm_model(
        issue=issue,
        upvotes=counts["upvote"],
        duplicates=counts["duplicate_flag"],
        spams=counts["spam_flag"],
        comments=comments_count,
        is_followed=is_followed
    )



# Need to select statement inside helper
from sqlalchemy import select


@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def create_issue(
    request: Request,  # Required by slowapi
    background_tasks: BackgroundTasks,
    title: str = Form(..., max_length=100),
    description: str = Form(..., max_length=2000),
    latitude: float = Form(...),
    longitude: float = Form(...),
    category_hint: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    video: Optional[UploadFile] = Form(None),  # Form fallback or File upload
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a new civic issue. Rate-limited to 5/hour per user."""
    # Filter empty uploads
    valid_images = [img for img in images if img.filename]
    
    # Handle optional video file
    video_file = None
    if video and isinstance(video, UploadFile) and video.filename:
        video_file = video

    issue = await issue_service.create_issue(
        reporter_id=current_user.id,
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        category_hint=category_hint,
        image_files=valid_images[:5],
        video_file=video_file,
        bg_tasks=background_tasks,
        db=db
    )
    
    return await build_issue_response(db, issue)


@router.get("", response_model=IssueListResponse)
async def list_issues(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None, description="minLat,minLng,maxLat,maxLng"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve list of issues with optional filters and pagination."""
    bbox_tuple = None
    if bbox:
        try:
            bbox_tuple = tuple(map(float, bbox.split(",")))
            if len(bbox_tuple) != 4:
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bounding box format. Must be minLat,minLng,maxLat,maxLng"
            )

    region_id_filter = None
    state_id_filter = None
    if current_user:
        if current_user.role == "admin":
            if current_user.admin_scope == "district":
                region_id_filter = current_user.region_id
            elif current_user.admin_scope == "state":
                state_id_filter = current_user.region_id
        elif current_user.role == "citizen":
            if current_user.region_id:
                region_id_filter = current_user.region_id
            elif current_user.state_id:
                state_id_filter = current_user.state_id

    offset = (page - 1) * limit
    issues, total = await issue_repo.get_paginated(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        category=category,
        severity=severity,
        bbox=bbox_tuple,
        region_id=region_id_filter,
        state_id=state_id_filter
    )

    items = [await build_issue_response(db, issue, current_user) for issue in issues]
    return IssueListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/{id}", response_model=IssueResponse)
async def get_issue(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get complete details of a specific issue by ID."""
    issue = await issue_repo.get_by_id(db, id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    return await build_issue_response(db, issue, current_user)



@router.post("/{id}/verify", response_model=VerificationResponse)
@limiter.limit("3/hour")
async def verify_issue(
    request: Request,  # Required by slowapi
    id: uuid.UUID,
    payload: VerificationCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upvote or flag an issue (duplicate/spam). Limit to 3 submissions/hour."""
    await issue_service.verify_issue(
        user_id=current_user.id,
        issue_id=id,
        verification_type=payload.type,
        bg_tasks=background_tasks,
        db=db
    )
    
    # Return verification record structure for matching schema
    return VerificationResponse(
        id=uuid.uuid4(),
        issue_id=id,
        user_id=current_user.id,
        type=payload.type
    )


@router.get("/{id}/comments", response_model=List[CommentResponse])
async def get_comments(
    id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve comments for a specific issue, paginated."""
    issue = await issue_repo.get_by_id(db, id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    offset = (page - 1) * limit
    comments, total = await issue_repo.get_comments_paginated(db, id, limit, offset)
    
    return [
        CommentResponse(
            id=c.id,
            issue_id=c.issue_id,
            user_id=c.user_id,
            user_name=c.user.name if c.user else "Deleted User",
            content=c.content,
            created_at=c.created_at
        )
        for c in comments
    ]


@router.post("/{id}/comments", response_model=CommentResponse)
async def create_comment(
    id: uuid.UUID,
    payload: CommentCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment/discussion post to an issue."""
    comment = await issue_service.add_comment(
        user_id=current_user.id,
        issue_id=id,
        text=payload.content,
        bg_tasks=background_tasks,
        db=db
    )
    
    return CommentResponse(
        id=comment.id,
        issue_id=comment.issue_id,
        user_id=comment.user_id,
        user_name=current_user.name,
        content=comment.content,
        created_at=comment.created_at
    )


@router.post("/{id}/follow", status_code=status.HTTP_200_OK)
async def follow_issue(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscribe to receive email notifications when the issue status changes."""
    issue = await issue_repo.get_by_id(db, id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
        
    from app.models.issue_follower import IssueFollower
    # Check if already followed
    stmt = select(IssueFollower).where(
        IssueFollower.issue_id == id,
        IssueFollower.user_id == current_user.id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    
    if not existing:
        follow = IssueFollower(issue_id=id, user_id=current_user.id)
        db.add(follow)
        await db.commit()
        
    return {"message": "Successfully subscribed to issue status updates."}


@router.delete("/{id}/follow", status_code=status.HTTP_200_OK)
async def unfollow_issue(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unsubscribe from issue status changes."""
    from app.models.issue_follower import IssueFollower
    stmt = select(IssueFollower).where(
        IssueFollower.issue_id == id,
        IssueFollower.user_id == current_user.id
    )
    res = await db.execute(stmt)
    existing = res.scalars().first()
    
    if existing:
        await db.delete(existing)
        await db.commit()
        
    return {"message": "Successfully unsubscribed from issue status updates."}

