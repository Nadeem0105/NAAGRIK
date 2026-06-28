# f:\CN Hackathon\backend\app\models\department.py
import uuid
from sqlalchemy import String, ARRAY, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # List of categories mapping to this department, e.g. ["pothole", "road_damage"]
    category_mapping: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    # Optional: scope to a specific region (NULL = global/shared department)
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    users = relationship("User", back_populates="department")
    issues = relationship("Issue", back_populates="assigned_department")
