from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
