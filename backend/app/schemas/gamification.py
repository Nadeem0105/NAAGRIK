import uuid
from datetime import datetime
from pydantic import BaseModel


class LeaderboardScope(BaseModel):
    type: str  # "state" | "global"
    state_id: uuid.UUID | None = None
    state_name: str | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    display_name: str
    avatar_url: str | None = None
    civic_points: int
    badge_count: int
    issues_reported: int
    issues_verified: int
    role: str


class ViewerRank(BaseModel):
    rank: int | None = None
    civic_points: int


class LeaderboardResponse(BaseModel):
    scope: LeaderboardScope
    entries: list[LeaderboardEntry]
    viewer_rank: ViewerRank | None = None


class StateResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    badge_id: uuid.UUID
    name: str
    description: str
    earned_at: datetime

    class Config:
        from_attributes = True
