from typing import List, Dict, Any
from app.repositories.evidence import EvidenceRepository
from app.services.debt import DebtService
from app.services.storage import StorageService
from app.core.exceptions import NotFoundException


class EvidenceService:
    def __init__(self):
        self.repo = EvidenceRepository()
        self.debt_service = DebtService()
        self.storage = StorageService()

    async def get_evidences(self, debt_id: str, user_id: str) -> List[Dict[str, Any]]:
        await self.debt_service.get_debt_by_id(debt_id, user_id)
        evidences = await self.repo.get_evidences_by_debt(debt_id, user_id)
        for ev in evidences:
            if ev.get("file_path"):
                ev["signed_url"] = self.storage.get_signed_url("evidences", ev["file_path"])
        return evidences

    async def upload_evidence(
        self,
        debt_id: str,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        description: str = None
    ) -> Dict[str, Any]:
        await self.debt_service.get_debt_by_id(debt_id, user_id)
        file_path, signed_url = self.storage.upload_file("evidences", user_id, file_bytes, filename, content_type)

        data = {
            "debt_id": debt_id,
            "user_id": user_id,
            "file_name": filename,
            "file_path": file_path,
            "file_type": content_type,
            "file_size": len(file_bytes),
            "description": description
        }

        created = await self.repo.create(data)
        created["signed_url"] = signed_url
        return created

    async def delete_evidence(self, evidence_id: str, user_id: str) -> bool:
        ev = await self.repo.get_by_id(evidence_id, user_id)
        if not ev:
            raise NotFoundException("Bukti transaksi tidak ditemukan")

        file_path = ev.get("file_path")
        if file_path:
            self.storage.delete_file("evidences", file_path)

        return await self.repo.delete(evidence_id, user_id)
