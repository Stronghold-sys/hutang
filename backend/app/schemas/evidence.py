from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: str
    debt_id: str
    user_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    signed_url: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
