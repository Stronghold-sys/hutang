from typing import List, Dict, Any
from app.repositories.notification import NotificationRepository
from app.core.exceptions import NotFoundException


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    async def get_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.repo.get_user_notifications(user_id)

    async def mark_as_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        notif = await self.repo.get_by_id(notification_id, user_id)
        if not notif:
            raise NotFoundException("Notifikasi tidak ditemukan")
        return await self.repo.update(notification_id, {"is_read": True, "read_at": "now()"}, user_id) or notif

    async def mark_all_as_read(self, user_id: str) -> bool:
        return await self.repo.mark_all_read(user_id)

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        notif = await self.repo.get_by_id(notification_id, user_id)
        if not notif:
            raise NotFoundException("Notifikasi tidak ditemukan")
        return await self.repo.delete(notification_id, user_id)
