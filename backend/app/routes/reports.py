from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Response
from app.schemas.common import APIResponse
from app.services.report import ReportService
from app.services.debt import DebtService
from app.services.payment import PaymentService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])
report_service = ReportService()
debt_service = DebtService()
payment_service = PaymentService()


@router.get("/summary", response_model=APIResponse)
async def report_summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await report_service.get_summary(current_user["id"])
    return APIResponse(
        success=True,
        message="Ringkasan laporan berhasil diambil",
        data=data
    )


@router.get("/debts", response_model=APIResponse)
async def report_debts(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    result = await debt_service.get_debts(user_id=current_user["id"], limit=1000)
    return APIResponse(
        success=True,
        message="Laporan utang/piutang berhasil diambil",
        data=result["items"]
    )


@router.get("/payments", response_model=APIResponse)
async def report_payments(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    result = await debt_service.get_debts(user_id=current_user["id"], limit=1000)
    debts = result.get("items", [])
    all_payments = []
    for d in debts:
        pays = await payment_service.get_debt_payments(d["id"], current_user["id"])
        all_payments.extend(pays)

    return APIResponse(
        success=True,
        message="Laporan riwayat pembayaran berhasil diambil",
        data=all_payments
    )


@router.get("/export")
async def export_report(
    format: Optional[str] = Query("xlsx"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    content, media_type, filename = await report_service.export_report(current_user["id"], format or "xlsx")
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return Response(content=content, media_type=media_type, headers=headers)

