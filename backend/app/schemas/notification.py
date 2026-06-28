import uuid
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    issue_id: uuid.UUID | None
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
