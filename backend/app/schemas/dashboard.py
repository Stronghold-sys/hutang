from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.debt import DebtResponse


class SummaryResponse(BaseModel):
    total_piutang: Decimal
    total_utang: Decimal
    saldo_bersih: Decimal
    jumlah_orang_berutang: int
    jumlah_utang_aktif: int


class CashFlowItem(BaseModel):
    label: str
    inflow: Decimal
    outflow: Decimal


class DashboardSummary(BaseModel):
    summary: SummaryResponse
    upcoming_due_dates: List[DebtResponse]
    recent_activities: List[dict]
