from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_date: Optional[datetime] = None
    payment_method: str = "cash"
    notes: Optional[str] = None
    evidence_url: Optional[str] = None
    idempotency_key: Optional[str] = None


class PaymentUpdateRequest(BaseModel):
    notes: Optional[str] = None
    evidence_url: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    debt_id: str
    user_id: str
    amount: Decimal
    payment_date: datetime
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = None
    evidence_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
