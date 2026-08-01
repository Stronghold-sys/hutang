from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.schemas.common import APIResponse, dump_model
from app.schemas.payment import PaymentCreateRequest, PaymentUpdateRequest
from app.services.payment import PaymentService
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["Payments"])
payment_service = PaymentService()


@router.get("/debts/{debt_id}/payments", response_model=APIResponse)
async def list_debt_payments(
    debt_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    payments = await payment_service.get_debt_payments(debt_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Riwayat pembayaran berhasil diambil",
        data=payments
    )


@router.post("/debts/{debt_id}/payments", response_model=APIResponse)
async def create_payment(
    debt_id: str,
    req: PaymentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    payment = await payment_service.create_payment(
        debt_id=debt_id,
        user_id=current_user["id"],
        payload=dump_model(req)
    )
    return APIResponse(
        success=True,
        message="Pembayaran berhasil dicatat",
        data=payment
    )


@router.get("/payments/{payment_id}", response_model=APIResponse)
async def get_payment(
    payment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    payment = await payment_service.get_payment_by_id(payment_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Detail pembayaran berhasil diambil",
        data=payment
    )


@router.patch("/payments/{payment_id}", response_model=APIResponse)
async def update_payment(
    payment_id: str,
    req: PaymentUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    clean_data = dump_model(req, exclude_unset=True)
    updated = await payment_service.repo.update(payment_id, clean_data, current_user["id"])
    return APIResponse(
        success=True,
        message="Data pembayaran berhasil diperbarui",
        data=updated
    )


@router.delete("/payments/{payment_id}", response_model=APIResponse)
async def delete_payment(
    payment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await payment_service.delete_payment(payment_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Pembayaran berhasil dihapus"
    )
