from typing import Dict, Any, Optional
from app.repositories.contact import ContactRepository
from app.core.exceptions import NotFoundException, ValidationException


class ContactService:
    def __init__(self):
        self.repo = ContactRepository()

    async def get_contacts(
        self,
        user_id: str,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        return await self.repo.get_user_contacts(user_id, search, page, limit, sort_by, sort_order)

    async def get_contact_by_id(self, contact_id: str, user_id: str) -> Dict[str, Any]:
        contact = await self.repo.get_by_id(contact_id, user_id)
        if not contact or contact.get("deleted_at") is not None:
            raise NotFoundException("Kontak tidak ditemukan")
        return contact

    async def create_contact(self, user_id: str, name: str, phone: Optional[str] = None, email: Optional[str] = None, address: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        if not name or not name.strip():
            raise ValidationException("Nama kontak wajib diisi")

        existing = await self.repo.find_by_name(user_id, name.strip())
        if existing:
            return existing

        data = {
            "user_id": user_id,
            "name": name.strip(),
            "phone": phone,
            "email": email,
            "address": address,
            "notes": notes
        }
        return await self.repo.create(data)

    async def update_contact(self, contact_id: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        await self.get_contact_by_id(contact_id, user_id)
        clean_data = {k: v for k, v in data.items() if v is not None}
        updated = await self.repo.update(contact_id, clean_data, user_id)
        return updated or {}
