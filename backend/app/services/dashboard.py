from decimal import Decimal
from typing import Dict, Any, List
from datetime import date
from urllib.parse import quote
from app.repositories.debt import DebtRepository
from app.repositories.activity_log import ActivityLogRepository
from app.core.config import settings
from app.services.auth import http_request


class DashboardService:
    def __init__(self):
        self.debt_repo = DebtRepository()
        self.log_repo = ActivityLogRepository()

    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        res = await self.debt_repo.get_user_debts(user_id=user_id, limit=500)
        items = res.get("items", [])

        total_piutang = Decimal("0.00")
        total_utang = Decimal("0.00")
        orang_berutang_set = set()
        jumlah_utang_aktif = 0

        for item in items:
            status = item.get("status")
            if status not in ["paid", "cancelled"]:
                t_type = item.get("type")
                rem = Decimal(str(item.get("remaining_amount", 0)))
                jumlah_utang_aktif += 1

                if t_type == "receivable":
                    total_piutang += rem
                    contact_id = item.get("contact_id")
                    if contact_id:
                        orang_berutang_set.add(contact_id)
                elif t_type == "payable":
                    total_utang += rem

        saldo_bersih = total_piutang - total_utang

        return {
            "total_piutang": float(total_piutang),
            "total_utang": float(total_utang),
            "saldo_bersih": float(saldo_bersih),
            "jumlah_orang_berutang": len(orang_berutang_set),
            "jumlah_utang_aktif": jumlah_utang_aktif
        }

    async def get_upcoming_due_dates(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        res = await self.debt_repo.get_user_debts(
            user_id=user_id,
            limit=limit,
            sort_by="due_date",
            sort_order="asc"
        )
        items = res.get("items", [])
        return [i for i in items if i.get("status") not in ["paid", "cancelled"]]

    async def get_recent_activities(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        url = f"{settings.SUPABASE_URL}/rest/v1/activity_logs?select=*&user_id=eq.{quote(str(user_id))}&order=created_at.desc&limit={limit}"
        status, data = await http_request(url, method="GET", headers=self.log_repo._get_headers())
        return data if isinstance(data, list) else []

    async def get_cash_flow(self, user_id: str) -> List[Dict[str, Any]]:
        res = await self.debt_repo.get_user_debts(user_id=user_id, limit=500)
        items = res.get("items", [])
        inflow = sum(float(i.get("paid_amount", 0)) for i in items if i.get("type") == "receivable")
        outflow = sum(float(i.get("paid_amount", 0)) for i in items if i.get("type") == "payable")
        return [
            {"label": "Total Cash Flow", "inflow": inflow, "outflow": outflow}
        ]
