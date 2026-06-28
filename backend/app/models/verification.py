import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Verification(Base):
    __tablename__ = "issue_verifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    issue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("issues.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # type: 'upvote', 'duplicate_flag', 'spam_flag'
    type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    issue = relationship("Issue", back_populates="verifications")
    user = relationship("User", back_populates="verifications")

    # A user can only upvote/flag an issue once
    __table_args__ = (
        UniqueConstraint("issue_id", "user_id", "type", name="uq_issue_user_verification_type"),
    )
