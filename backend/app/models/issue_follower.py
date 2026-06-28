import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class IssueFollower(Base):
    __tablename__ = "issue_followers"

    issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    issue = relationship("Issue", back_populates="followers")
    user = relationship("User", back_populates="followed_issues")
