from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class ProfileResponse(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    timezone: str = "Asia/Jakarta"
    currency: str = "IDR"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
