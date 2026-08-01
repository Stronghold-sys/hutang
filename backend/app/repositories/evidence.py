from typing import List, Dict, Any
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.services.auth import http_request


class EvidenceRepository(BaseRepository):
    def __init__(self):
        super().__init__("debt_evidences")

    async def get_evidences_by_debt(self, debt_id: str, user_id: str) -> List[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&debt_id=eq.{quote(str(debt_id))}&user_id=eq.{quote(str(user_id))}&order=created_at.desc"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        return data if isinstance(data, list) else []
