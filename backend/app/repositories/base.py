from typing import Dict, Any, List, Optional
from urllib.parse import quote
from app.core.config import settings
from app.core.logging import logger
from app.services.auth import http_request


class BaseRepository:
    def __init__(self, table_name: str):
        self.table_name = table_name

    def _get_headers(self, prefer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def get_by_id(self, id_val: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?id=eq.{quote(str(id_val))}"
        if user_id:
            url += f"&user_id=eq.{quote(str(user_id))}"
        status, data = await http_request(url, method="GET", headers=self._get_headers())
        if status == 200 and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}"
        headers = self._get_headers(prefer="return=representation")
        status, res_data = await http_request(url, method="POST", headers=headers, body=data)
        if status in (200, 201) and isinstance(res_data, list) and len(res_data) > 0:
            return res_data[0]
        return data

    async def update(self, id_val: str, data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?id=eq.{quote(str(id_val))}"
        if user_id:
            url += f"&user_id=eq.{quote(str(user_id))}"
        headers = self._get_headers(prefer="return=representation")
        status, res_data = await http_request(url, method="PATCH", headers=headers, body=data)
        if status == 200 and isinstance(res_data, list) and len(res_data) > 0:
            return res_data[0]
        return None

    async def delete(self, id_val: str, user_id: Optional[str] = None, soft_delete: bool = False) -> bool:
        if soft_delete:
            from datetime import datetime
            res = await self.update(id_val, {"deleted_at": datetime.now().isoformat()}, user_id)
            return bool(res)
        url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?id=eq.{quote(str(id_val))}"
        if user_id:
            url += f"&user_id=eq.{quote(str(user_id))}"
        status, _ = await http_request(url, method="DELETE", headers=self._get_headers())
        return status in (200, 204)
