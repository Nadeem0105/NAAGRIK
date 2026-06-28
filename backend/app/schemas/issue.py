import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, examples=["I can confirm this pothole is huge!"])


class CommentResponse(BaseModel):
    id: uuid.UUID
    issue_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class VerificationCreateRequest(BaseModel):
    type: str = Field(..., examples=["upvote", "duplicate_flag", "spam_flag"])

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = ["upvote", "duplicate_flag", "spam_flag"]
        if v not in allowed:
            raise ValueError(f"Type must be one of: {', '.join(allowed)}")
        return v


class VerificationResponse(BaseModel):
    id: uuid.UUID
    issue_id: uuid.UUID
    user_id: uuid.UUID
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    id: uuid.UUID
    reporter_id: Optional[uuid.UUID] = None
    reporter_name: Optional[str] = "Anonymous"
    title: str
    description: str
    category: str
    severity: str
    status: str
    address: Optional[str] = None
    image_urls: List[str] = []
    video_url: Optional[str] = None
    assigned_department_id: Optional[uuid.UUID] = None
    assigned_department_name: Optional[str] = None
    assigned_to_user_id: Optional[uuid.UUID] = None
    assigned_to_user_name: Optional[str] = None
    duplicate_of_issue_id: Optional[uuid.UUID] = None
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_image_url: Optional[str] = None
    sla_due_at: Optional[datetime] = None
    is_followed: Optional[bool] = False
    region_id: Optional[uuid.UUID] = None
    
    # Location coordinates exposed to client
    latitude: float
    longitude: float
    
    # Aggregated verification stats
    upvotes_count: int = 0
    duplicate_flags_count: int = 0
    spam_flags_count: int = 0
    comments_count: int = 0

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_model(cls, issue, upvotes=0, duplicates=0, spams=0, comments=0, is_followed=False):
        return cls(
            id=issue.id,
            reporter_id=issue.reporter_id,
            reporter_name=issue.reporter.name if issue.reporter else "Anonymous",
            title=issue.title,
            description=issue.description,
            category=issue.category,
            severity=issue.severity,
            status=issue.status,
            address=issue.address,
            image_urls=issue.image_urls,
            video_url=issue.video_url,
            assigned_department_id=issue.assigned_department_id,
            assigned_department_name=issue.assigned_department.name if issue.assigned_department else None,
            assigned_to_user_id=issue.assigned_to_user_id,
            assigned_to_user_name=issue.assigned_user.name if issue.assigned_user else None,
            duplicate_of_issue_id=issue.duplicate_of_issue_id,
            ai_confidence=issue.ai_confidence,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            resolved_at=issue.resolved_at,
            resolution_image_url=issue.resolution_image_url,
            sla_due_at=issue.sla_due_at,
            is_followed=is_followed,
            region_id=issue.region_id,
            latitude=issue.latitude,
            longitude=issue.longitude,
            upvotes_count=upvotes,
            duplicate_flags_count=duplicates,
            spam_flags_count=spams,
            comments_count=comments
        )



class IssueListResponse(BaseModel):
    items: List[IssueResponse]
    total: int
    page: int
    limit: int


class IssueUpdateRequest(BaseModel):
    status: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    assigned_department_id: Optional[uuid.UUID] = None
    assigned_to_user_id: Optional[uuid.UUID] = None
    duplicate_of_issue_id: Optional[uuid.UUID] = None
    resolution_image_url: Optional[str] = None
    sla_due_at: Optional[datetime] = None


    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = ["reported", "verified", "assigned", "in_progress", "resolved"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = ["low", "medium", "high"]
        if v not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(allowed)}")
        return v
