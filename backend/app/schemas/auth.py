import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.region import RegionResponse


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    password: str = Field(..., min_length=6, max_length=128, examples=["secret123"])
    state_id: Optional[uuid.UUID] = None


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    password: str = Field(..., examples=["secret123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str
    points: int
    created_at: datetime
    department_id: uuid.UUID | None = None
    admin_scope: str | None = None
    region_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    region: Optional[RegionResponse] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "citizen",
                "points": 10,
                "created_at": "2026-06-25T12:00:00Z",
                "department_id": None
            }
        }


class UpdateStateRequest(BaseModel):
    state_id: uuid.UUID
