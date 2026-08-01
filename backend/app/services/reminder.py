from typing import List, Dict, Any
from app.repositories.reminder import ReminderRepository
from app.services.debt import DebtService
from app.core.exceptions import NotFoundException


class ReminderService:
    def __init__(self):
        self.repo = ReminderRepository()
        self.debt_service = DebtService()

    async def get_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.repo.get_user_reminders(user_id)

    async def create_reminder(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        debt_id = payload.get("debt_id")
        await self.debt_service.get_debt_by_id(debt_id, user_id)

        data = {
            "user_id": user_id,
            "debt_id": debt_id,
            "reminder_date": payload.get("reminder_date").isoformat(),
            "reminder_type": payload.get("reminder_type", "due_date"),
            "message": payload.get("message"),
            "status": "pending"
        }
        return await self.repo.create(data)

    async def update_reminder(self, reminder_id: str, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        rem = await self.repo.get_by_id(reminder_id, user_id)
        if not rem:
            raise NotFoundException("Pengingat tidak ditemukan")

        clean_data = {k: v for k, v in payload.items() if v is not None}
        if "reminder_date" in clean_data:
            clean_data["reminder_date"] = clean_data["reminder_date"].isoformat()

        return await self.repo.update(reminder_id, clean_data, user_id) or rem

    async def delete_reminder(self, reminder_id: str, user_id: str) -> bool:
        rem = await self.repo.get_by_id(reminder_id, user_id)
        if not rem:
            raise NotFoundException("Pengingat tidak ditemukan")
        return await self.repo.delete(reminder_id, user_id)
