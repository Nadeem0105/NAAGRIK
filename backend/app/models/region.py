# f:\CN Hackathon\backend\app\models\region.py
import uuid
from sqlalchemy import String, ForeignKey, CheckConstraint, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Region(Base):
    __tablename__ = "regions"

    __table_args__ = (
        CheckConstraint("type IN ('state', 'district')", name="ck_region_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)  # 'state' or 'district'
    parent_region_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True
    )

    bbox_south: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_north: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_west: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_east: Mapped[float | None] = mapped_column(Float, nullable=True)
    boundary_geojson: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Self-referential: districts point to their parent state
    parent = relationship("Region", remote_side=[id], backref="children")

    @property
    def bbox(self) -> dict | None:
        if self.bbox_south is not None:
            return {
                "south": self.bbox_south,
                "north": self.bbox_north,
                "west": self.bbox_west,
                "east": self.bbox_east
            }
        return None
