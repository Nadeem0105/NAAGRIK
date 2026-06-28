import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Roads"])
    category_mapping: List[str] = Field(default=[], examples=[["pothole", "road_damage"]])
    region_id: Optional[uuid.UUID] = Field(default=None, description="Optional region binding")


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    category_mapping: Optional[List[str]] = Field(default=None)
    region_id: Optional[uuid.UUID] = Field(default=None)


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    category_mapping: List[str]
    region_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

