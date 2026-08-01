from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.schemas.common import APIResponse
from app.services.notification import NotificationService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])
notif_service = NotificationService()


@router.get("", response_model=APIResponse)
async def list_notifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    notifications = await notif_service.get_notifications(current_user["id"])
    return APIResponse(
        success=True,
        message="Daftar notifikasi berhasil diambil",
        data=notifications
    )


@router.patch("/{notification_id}/read", response_model=APIResponse)
async def mark_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    notif = await notif_service.mark_as_read(notification_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Notifikasi ditandai dibaca",
        data=notif
    )


@router.patch("/read-all", response_model=APIResponse)
async def mark_all_read(current_user: Dict[str, Any] = Depends(get_current_user)):
    await notif_service.mark_all_as_read(current_user["id"])
    return APIResponse(
        success=True,
        message="Semua notifikasi ditandai dibaca"
    )


@router.delete("/{notification_id}", response_model=APIResponse)
async def delete_notification(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await notif_service.delete_notification(notification_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Notifikasi berhasil dihapus"
    )
