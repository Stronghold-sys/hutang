from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.repositories.payment import PaymentRepository
from app.services.debt import DebtService
from app.core.exceptions import ValidationException, NotFoundException, ConflictException
from app.repositories.activity_log import ActivityLogRepository


class PaymentService:
    def __init__(self):
        self.repo = PaymentRepository()
        self.debt_service = DebtService()
        self.log_repo = ActivityLogRepository()

    async def get_debt_payments(self, debt_id: str, user_id: str) -> List[Dict[str, Any]]:
        await self.debt_service.get_debt_by_id(debt_id, user_id)
        return await self.repo.get_payments_by_debt(debt_id, user_id)

    async def get_payment_by_id(self, payment_id: str, user_id: str) -> Dict[str, Any]:
        payment = await self.repo.get_by_id(payment_id, user_id)
        if not payment or payment.get("deleted_at") is not None:
            raise NotFoundException("Pembayaran tidak ditemukan")
        return payment

    async def create_payment(self, debt_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        amount = Decimal(str(payload.get("amount", 0)))
        if amount <= 0:
            raise ValidationException("Nominal pembayaran harus lebih besar dari 0")

        # Idempotency check
        idempotency_key = payload.get("idempotency_key")
        if idempotency_key:
            existing_pay = await self.repo.get_by_idempotency_key(idempotency_key, user_id)
            if existing_pay:
                return existing_pay

        debt = await self.debt_service.get_debt_by_id(debt_id, user_id)
        remaining = Decimal(str(debt.get("remaining_amount", 0)))

        if amount > remaining:
            raise ValidationException(f"Nominal pembayaran (Rp {amount:,.0f}) melebihi sisa utang (Rp {remaining:,.0f})")

        payment_date = payload.get("payment_date") or datetime.now()
        data = {
            "debt_id": debt_id,
            "user_id": user_id,
            "amount": float(amount),
            "payment_date": payment_date.isoformat() if isinstance(payment_date, datetime) else payment_date,
            "payment_method": payload.get("payment_method", "cash"),
            "notes": payload.get("notes"),
            "evidence_url": payload.get("evidence_url"),
            "idempotency_key": idempotency_key
        }

        created = await self.repo.create(data)

        # Update debt balances manually in app layer (also backed up by SQL trigger in Supabase)
        new_paid = Decimal(str(debt.get("paid_amount", 0))) + amount
        new_remaining = remaining - amount
        new_status = "paid" if new_remaining == 0 else "partially_paid"

        await self.debt_service.repo.update(debt_id, {
            "paid_amount": float(new_paid),
            "remaining_amount": float(new_remaining),
            "status": new_status
        }, user_id)

        await self.log_repo.log_action(
            user_id=user_id,
            action="CREATE_PAYMENT",
            entity_type="payment",
            entity_id=created.get("id"),
            new_data=created
        )

        return created

    async def delete_payment(self, payment_id: str, user_id: str) -> bool:
        payment = await self.get_payment_by_id(payment_id, user_id)
        debt_id = payment.get("debt_id")
        amount = Decimal(str(payment.get("amount", 0)))

        debt = await self.debt_service.get_debt_by_id(debt_id, user_id)
        new_paid = Decimal(str(debt.get("paid_amount", 0))) - amount
        if new_paid < 0:
            new_paid = Decimal("0.00")
        
        principal = Decimal(str(debt.get("principal_amount", 0)))
        new_remaining = principal - new_paid
        new_status = "active" if new_paid == 0 else "partially_paid"

        await self.debt_service.repo.update(debt_id, {
            "paid_amount": float(new_paid),
            "remaining_amount": float(new_remaining),
            "status": new_status
        }, user_id)

        return await self.repo.delete(payment_id, user_id, soft_delete=True)
