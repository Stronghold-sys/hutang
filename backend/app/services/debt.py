from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import date, datetime
from app.repositories.debt import DebtRepository
from app.services.contact import ContactService
from app.core.exceptions import NotFoundException, ValidationException, AppException
from app.repositories.activity_log import ActivityLogRepository


class DebtService:
    def __init__(self):
        self.repo = DebtRepository()
        self.contact_service = ContactService()
        self.log_repo = ActivityLogRepository()

    async def get_debts(
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
        return await self.repo.get_user_debts(
            user_id=user_id,
            search=search,
            debt_type=debt_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            due_status=due_status,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

    async def get_debt_by_id(self, debt_id: str, user_id: str) -> Dict[str, Any]:
        debt = await self.repo.get_by_id(debt_id, user_id)
        if not debt or debt.get("deleted_at") is not None:
            raise NotFoundException("Catatan utang/piutang tidak ditemukan")

        if debt.get("contact_id"):
            try:
                contact = await self.contact_service.get_contact_by_id(debt["contact_id"], user_id)
                debt["contact"] = contact
            except Exception:
                debt["contact"] = None

        return debt

    async def create_debt(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        principal = Decimal(str(payload.get("principal_amount", 0)))
        if principal <= 0:
            raise ValidationException("Nominal pokok harus lebih besar dari 0")

        contact_id = payload.get("contact_id")
        if not contact_id and payload.get("contact_name"):
            c = await self.contact_service.create_contact(
                user_id=user_id,
                name=payload.get("contact_name"),
                phone=payload.get("contact_phone"),
                address=payload.get("contact_address")
            )
            contact_id = c.get("id")

        if not contact_id:
            raise ValidationException("Kontak wajib dipilih atau diisi")

        interest_type = payload.get("interest_type", "none")
        interest_val = Decimal(str(payload.get("interest_value", 0)))
        late_fee = Decimal(str(payload.get("late_fee", 0)))

        interest_amount = Decimal("0.00")
        if interest_type == "percentage":
            interest_amount = (principal * interest_val / Decimal("100.00"))
        elif interest_type == "fixed":
            interest_amount = interest_val

        total_due = principal + interest_amount + late_fee
        title = payload.get("title") or payload.get("description") or f"Transaksi {payload.get('type')}"

        data = {
            "user_id": user_id,
            "contact_id": contact_id,
            "type": payload.get("type"),
            "title": title,
            "description": payload.get("description"),
            "principal_amount": float(principal),
            "paid_amount": 0.0,
            "remaining_amount": float(total_due),
            "status": "active",
            "transaction_date": (payload.get("transaction_date") or date.today()).isoformat() if isinstance(payload.get("transaction_date"), (date, datetime)) else payload.get("transaction_date") or date.today().isoformat(),
            "due_date": payload.get("due_date").isoformat() if isinstance(payload.get("due_date"), (date, datetime)) else payload.get("due_date"),
            "currency": payload.get("currency", "IDR"),
            "interest_type": interest_type,
            "interest_value": float(interest_val),
            "late_fee": float(late_fee),
            "reminder_enabled": payload.get("reminder_enabled", False)
        }

        debt = await self.repo.create(data)
        return debt

    async def update_debt(self, debt_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        existing = await self.get_debt_by_id(debt_id, user_id)
        if existing.get("status") == "paid":
            raise ValidationException("Transaksi yang sudah lunas tidak dapat diubah")

        clean_payload = {k: v for k, v in payload.items() if v is not None}
        updated = await self.repo.update(debt_id, clean_payload, user_id)
        return updated or existing

    async def delete_debt(self, debt_id: str, user_id: str) -> bool:
        await self.get_debt_by_id(debt_id, user_id)
        return await self.repo.delete(debt_id, user_id, soft_delete=True)
