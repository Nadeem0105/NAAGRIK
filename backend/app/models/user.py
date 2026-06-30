# f:\CN Hackathon\backend\app\models\user.py
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "admin_scope IN ('district', 'state', 'super') OR admin_scope IS NULL",
            name="ck_user_admin_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String, default="password", server_default="password", nullable=False)
    google_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String, default="citizen")  # citizen, admin
    department_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Jurisdictional scope — NULL for citizens and super-admins with global access
    admin_scope: Mapped[str | None] = mapped_column(String, nullable=True)  # 'district', 'state', 'super'
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )
    state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    department = relationship("Department", back_populates="users")
    region = relationship("Region", foreign_keys=[region_id])
    state = relationship("Region", foreign_keys=[state_id])
    issues_reported = relationship("Issue", foreign_keys="[Issue.reporter_id]", back_populates="reporter")
    issues_assigned = relationship("Issue", foreign_keys="[Issue.assigned_to_user_id]", back_populates="assigned_user")
    verifications = relationship("Verification", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    status_changes = relationship("StatusHistory", back_populates="changed_by_user")
    notifications = relationship("Notification", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    followed_issues = relationship("IssueFollower", back_populates="user", cascade="all, delete-orphan")
