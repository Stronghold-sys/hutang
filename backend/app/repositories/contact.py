from typing import List, Dict, Any, Optional
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.core.logging import logger
from app.services.auth import http_request


class ContactRepository(BaseRepository):
    def __init__(self):
        super().__init__("contacts")

    async def get_user_contacts(
        self,
        user_id: str,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        try:
            desc = "desc" if sort_order.lower() == "desc" else "asc"
            offset = (page - 1) * limit
            url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&user_id=eq.{quote(str(user_id))}&deleted_at=is.null&order={sort_by}.{desc}&offset={offset}&limit={limit}"
            if search:
                url += f"&name=ilike.*{quote(str(search))}*"

            headers = self._get_headers(prefer="count=exact")
            status, data = await http_request(url, method="GET", headers=headers)
            items = data if isinstance(data, list) else []
            total = len(items)
            return {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit
            }
        except Exception as e:
            logger.warning(f"Error in get_user_contacts: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit}

    async def find_by_name(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*&user_id=eq.{quote(str(user_id))}&name=ilike.{quote(str(name))}&deleted_at=is.null"
            status, data = await http_request(url, method="GET", headers=self._get_headers())
            if status == 200 and isinstance(data, list) and len(data) > 0:
                return data[0]
        except Exception as e:
            logger.warning(f"Error in find_by_name: {e}")
        return None
