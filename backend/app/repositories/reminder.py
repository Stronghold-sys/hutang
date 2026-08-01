from typing import List, Dict, Any
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.services.auth import http_request


class ReminderRepository(BaseRepository):
    def __init__(self):
        super().__init__("reminders")

    async def get_user_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&user_id=eq.{quote(str(user_id))}&order=reminder_date.asc"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        return data if isinstance(data, list) else []
