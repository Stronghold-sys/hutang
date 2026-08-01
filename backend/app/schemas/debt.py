from typing import Optional, Literal
from decimal import Decimal
from pydantic import BaseModel, Field
try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator

from datetime import date, datetime
from app.schemas.contact import ContactResponse


class DebtCreateRequest(BaseModel):
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    type: str  # 'receivable', 'payable', 'Piutang', 'Utang'
    title: Optional[str] = None
    description: Optional[str] = None
    principal_amount: Decimal = Field(..., gt=0)
    transaction_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: str = "IDR"
    interest_type: Literal["none", "percentage", "fixed"] = "none"
    interest_value: Decimal = Field(default=Decimal("0.00"), ge=0)
    late_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    reminder_enabled: bool = False

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_str = str(v).strip().lower()
        if v_str in ["piutang", "receivable"]:
            return "receivable"
        elif v_str in ["utang", "payable"]:
            return "payable"
        raise ValueError("Tipe utang harus 'receivable'/'Piutang' atau 'payable'/'Utang'")


class DebtUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    principal_amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None
    status: Optional[str] = None
    interest_type: Optional[Literal["none", "percentage", "fixed"]] = None
    interest_value: Optional[Decimal] = Field(None, ge=0)
    late_fee: Optional[Decimal] = Field(None, ge=0)
    reminder_enabled: Optional[bool] = None


class DebtResponse(BaseModel):
    id: str
    user_id: str
    contact_id: str
    contact: Optional[ContactResponse] = None
    type: str
    title: str
    description: Optional[str] = None
    principal_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    status: str
    transaction_date: date
    due_date: Optional[date] = None
    currency: str
    interest_type: str
    interest_value: Decimal
    late_fee: Decimal
    reminder_enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
