# f:\CN Hackathon\backend\app\schemas\region.py
import uuid
from typing import List, Optional
from pydantic import BaseModel


class RegionCreate(BaseModel):
    name: str
    type: str          # 'state' or 'district'
    parent_region_id: Optional[uuid.UUID] = None


class RegionUpdate(BaseModel):
    name: Optional[str] = None


class RegionResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    parent_region_id: Optional[uuid.UUID] = None
    bbox: Optional[dict] = None
    boundary_geojson: Optional[dict] = None

    class Config:
        from_attributes = True


class RegionTree(RegionResponse):
    """Region with its children (districts) nested."""
    children: List[RegionResponse] = []


class AssignRegionRequest(BaseModel):
    admin_scope: str   # 'district', 'state', or 'super'
    region_id: Optional[uuid.UUID] = None  # NULL for super-admin
