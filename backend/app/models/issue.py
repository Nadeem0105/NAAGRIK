# f:\CN Hackathon\backend\app\models\issue.py
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, index=True, nullable=False)  # AI assigned, admin editable
    severity: Mapped[str] = mapped_column(String, default="medium")            # low, medium, high
    status: Mapped[str] = mapped_column(String, index=True, default="reported")  # reported, verified, assigned, etc.
    
    # Location coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    image_hashes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    assigned_department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    duplicate_of_issue_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("issues.id"), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Jurisdictional region — auto-set from reverse-geocoding at creation time
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Raw JSON response from AI model
    raw_ai_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="issues_reported")
    assigned_user = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="issues_assigned")
    assigned_department = relationship("Department", back_populates="issues")
    region = relationship("Region", foreign_keys=[region_id])
    
    # Self-referential relationship for duplicates
    duplicates = relationship("Issue", backref="duplicate_parent", remote_side=[id])
    
    verifications = relationship("Verification", back_populates="issue")
    comments = relationship("Comment", back_populates="issue")
    status_history = relationship("StatusHistory", back_populates="issue")
    followers = relationship("IssueFollower", back_populates="issue", cascade="all, delete-orphan")
