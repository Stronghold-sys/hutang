from typing import List, Dict, Any, Optional
from datetime import date
from urllib.parse import quote
from app.repositories.base import BaseRepository
from app.core.config import settings
from app.core.logging import logger
from app.services.auth import http_request


class DebtRepository(BaseRepository):
    def __init__(self):
        super().__init__("debts")

    async def get_user_debts(
        self,
        user_id: str,
        search: Optional[str] = None,
        debt_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        due_status: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        try:
            desc = "desc" if sort_order.lower() == "desc" else "asc"
            offset = (page - 1) * limit
            url = f"{settings.SUPABASE_URL}/rest/v1/{self.table_name}?select=*,contacts(*)&user_id=eq.{quote(str(user_id))}&deleted_at=is.null&order={sort_by}.{desc}&offset={offset}&limit={limit}"

            if search:
                url += f"&or=(title.ilike.*{quote(str(search))}*,description.ilike.*{quote(str(search))}*)"
            if debt_type:
                url += f"&type=eq.{quote(str(debt_type))}"
            if status:
                url += f"&status=eq.{quote(str(status))}"
            if start_date:
                url += f"&transaction_date=gte.{start_date.isoformat()}"
            if end_date:
                url += f"&transaction_date=lte.{end_date.isoformat()}"

            headers = self._get_headers(prefer="count=exact")
            req_status, data = await http_request(url, method="GET", headers=headers)
            items = data if isinstance(data, list) else []
            total = len(items)
            return {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit
            }
        except Exception as e:
            logger.warning(f"Error in get_user_debts: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit}
