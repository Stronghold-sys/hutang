from typing import List, Dict, Any
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.services.auth import http_request


class NotificationRepository(BaseRepository):
    def __init__(self):
        super().__init__("notifications")

    async def get_user_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&user_id=eq.{quote(str(user_id))}&order=created_at.desc"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        return data if isinstance(data, list) else []

    async def mark_all_read(self, user_id: str) -> bool:
        from datetime import datetime
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?user_id=eq.{quote(str(user_id))}&is_read=eq.false"
        headers = self._get_headers(prefer="return=minimal")
        status, _ = await http_request(url, method="PATCH", headers=headers, body={"is_read": True, "read_at": datetime.now().isoformat()})
        return status in (200, 204)
