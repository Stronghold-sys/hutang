from typing import Dict, Any, Optional
from app.repositories.base import BaseRepository
from app.services.storage import StorageService
from app.core.exceptions import NotFoundException, AppException


class ProfileService:
    def __init__(self):
        self.repo = BaseRepository("profiles")
        self.storage = StorageService()

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        profile = await self.repo.get_by_id(user_id)
        if not profile:
            raise NotFoundException("Profil pengguna tidak ditemukan")
        return profile

    async def update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        clean_data = {k: v for k, v in data.items() if v is not None}
        clean_data.pop("role", None)

        updated = await self.repo.update(user_id, clean_data)
        if not updated:
            clean_data["id"] = user_id
            updated = await self.repo.create(clean_data)
        return updated

    async def update_avatar(self, user_id: str, file_bytes: bytes, filename: str, content_type: str) -> str:
        profile = await self.get_profile(user_id)
        old_avatar = profile.get("avatar_url")

        file_path, avatar_url = self.storage.upload_file("avatars", user_id, file_bytes, filename, content_type)
        await self.repo.update(user_id, {"avatar_url": avatar_url})

        if old_avatar and "avatars/" in old_avatar:
            try:
                old_path = old_avatar.split("avatars/")[-1]
                self.storage.delete_file("avatars", old_path)
            except Exception:
                pass

        return avatar_url

    async def delete_avatar(self, user_id: str) -> bool:
        profile = await self.get_profile(user_id)
        old_avatar = profile.get("avatar_url")
        if old_avatar and "avatars/" in old_avatar:
            old_path = old_avatar.split("avatars/")[-1]
            self.storage.delete_file("avatars", old_path)

        await self.repo.update(user_id, {"avatar_url": None})
        return True

    async def delete_account(self, user_id: str) -> bool:
        try:
            await self.repo.delete(user_id)
            return True
        except Exception as e:
            raise AppException(message=f"Gagal menghapus akun: {str(e)}")
