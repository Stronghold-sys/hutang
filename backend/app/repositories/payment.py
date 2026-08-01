from typing import List, Dict, Any, Optional
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.services.auth import http_request


class PaymentRepository(BaseRepository):
    def __init__(self):
        super().__init__("debt_payments")

    async def get_payments_by_debt(self, debt_id: str, user_id: str) -> List[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&debt_id=eq.{quote(str(debt_id))}&user_id=eq.{quote(str(user_id))}&deleted_at=is.null&order=payment_date.desc"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        return data if isinstance(data, list) else []

    async def get_by_idempotency_key(self, key: str, user_id: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&idempotency_key=eq.{quote(str(key))}&user_id=eq.{quote(str(user_id))}"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        if status == 200 and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
