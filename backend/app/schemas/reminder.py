from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime


class ReminderCreateRequest(BaseModel):
    debt_id: str
    reminder_date: datetime
    reminder_type: Literal["due_date", "custom", "overdue"] = "due_date"
    message: str


class ReminderUpdateRequest(BaseModel):
    reminder_date: Optional[datetime] = None
    message: Optional[str] = None
    status: Optional[Literal["pending", "sent", "cancelled"]] = None


class ReminderResponse(BaseModel):
    id: str
    debt_id: str
    user_id: str
    reminder_date: datetime
    reminder_type: str
    message: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
