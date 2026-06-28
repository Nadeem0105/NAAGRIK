from typing import Dict, List
from pydantic import BaseModel


class ImpactResponse(BaseModel):
    total_reported: int
    total_resolved: int
    avg_resolution_time_hours: float
    category_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]


class HotspotResponse(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float
    issue_count: int
    top_category: str
    issue_ids: List[str]


class DepartmentPerformance(BaseModel):
    name: str
    assigned_count: int
    resolved_count: int
    resolution_rate: float
    avg_resolution_time_hours: float

