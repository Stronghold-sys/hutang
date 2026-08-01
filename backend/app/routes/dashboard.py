from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.schemas.common import APIResponse
from app.services.dashboard import DashboardService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/summary", response_model=APIResponse)
async def summary(current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await dashboard_service.get_summary(current_user["id"])
    return APIResponse(
        success=True,
        message="Ringkasan dashboard berhasil diambil",
        data=data
    )


@router.get("/cash-flow", response_model=APIResponse)
async def cash_flow(current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await dashboard_service.get_cash_flow(current_user["id"])
    return APIResponse(
        success=True,
        message="Data arus kas berhasil diambil",
        data=data
    )


@router.get("/upcoming-due-dates", response_model=APIResponse)
async def upcoming_due_dates(current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await dashboard_service.get_upcoming_due_dates(current_user["id"])
    return APIResponse(
        success=True,
        message="Daftar jatuh tempo terdekat berhasil diambil",
        data=data
    )


@router.get("/recent-activities", response_model=APIResponse)
async def recent_activities(current_user: Dict[str, Any] = Depends(get_current_user)):
    data = await dashboard_service.get_recent_activities(current_user["id"])
    return APIResponse(
        success=True,
        message="Aktivitas terbaru berhasil diambil",
        data=data
    )
