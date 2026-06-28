import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    # JSON structure storing badge criteria, e.g. {"type": "reports_count", "threshold": 10}
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    users = relationship("UserBadge", back_populates="badge")
