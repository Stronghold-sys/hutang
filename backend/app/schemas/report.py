from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.debt import DebtResponse
from app.schemas.payment import PaymentResponse


class ReportSummaryResponse(BaseModel):
    total_records: int
    total_piutang_active: Decimal
    total_utang_active: Decimal
    total_paid: Decimal
    total_overdue: Decimal


class ReportExportResponse(BaseModel):
    download_url: Optional[str] = None
    data_format: str
    record_count: int
    generated_at: str
