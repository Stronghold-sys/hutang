from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.schemas.common import APIResponse, dump_model
from app.schemas.reminder import ReminderCreateRequest, ReminderUpdateRequest
from app.services.reminder import ReminderService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders"])
reminder_service = ReminderService()


@router.get("", response_model=APIResponse)
async def list_reminders(current_user: Dict[str, Any] = Depends(get_current_user)):
    reminders = await reminder_service.get_reminders(current_user["id"])
    return APIResponse(
        success=True,
        message="Daftar pengingat berhasil diambil",
        data=reminders
    )


@router.post("", response_model=APIResponse)
async def create_reminder(
    req: ReminderCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    reminder = await reminder_service.create_reminder(current_user["id"], dump_model(req))
    return APIResponse(
        success=True,
        message="Pengingat berhasil dibuat",
        data=reminder
    )


@router.patch("/{reminder_id}", response_model=APIResponse)
async def update_reminder(
    reminder_id: str,
    req: ReminderUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = await reminder_service.update_reminder(reminder_id, current_user["id"], dump_model(req, exclude_unset=True))
    return APIResponse(
        success=True,
        message="Pengingat berhasil diperbarui",
        data=updated
    )


@router.delete("/{reminder_id}", response_model=APIResponse)
async def delete_reminder(
    reminder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await reminder_service.delete_reminder(reminder_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Pengingat berhasil dihapus"
    )
