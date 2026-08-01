import uuid
from typing import Tuple, Optional
from app.dependencies.db import get_supabase_admin_client
from app.core.config import settings
from app.core.exceptions import ValidationException, AppException
from app.core.logging import logger


class StorageService:
    def __init__(self):
        self.client = get_supabase_admin_client()

    def upload_file(
        self,
        bucket: str,
        user_id: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str
    ) -> Tuple[str, str]:
        """
        Uploads file to Supabase Storage and returns (file_path, public_or_signed_url)
        """
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValidationException(f"Ukuran file melebihi batas maksimal {settings.MAX_UPLOAD_SIZE_MB} MB")

        allowed_mime = [
            "image/jpeg", "image/png", "image/webp", "image/gif",
            "application/pdf", "image/svg+xml"
        ]
        if content_type not in allowed_mime:
            raise ValidationException(f"Tipe file '{content_type}' tidak diizinkan")

        ext = original_filename.split(".")[-1] if "." in original_filename else "bin"
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = f"{user_id}/{filename}"

        try:
            res = self.client.storage.from_(bucket).upload(
                file_path,
                file_bytes,
                file_options={"content-type": content_type}
            )
            
            # Generate URL or signed URL
            if bucket == "avatars":
                url = self.client.storage.from_(bucket).get_public_url(file_path)
            else:
                # Signed URL valid for 1 hour for evidence
                signed_res = self.client.storage.from_(bucket).create_signed_url(file_path, 3600)
                url = signed_res.get("signedUrl") if isinstance(signed_res, dict) else str(signed_res)

            return file_path, url
        except Exception as e:
            logger.error(f"Storage upload error: {e}")
            # Fallback mock path/url if Supabase is offline/mock
            mock_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"
            return file_path, mock_url

    def get_signed_url(self, bucket: str, file_path: str, expires_in: int = 3600) -> str:
        try:
            signed_res = self.client.storage.from_(bucket).create_signed_url(file_path, expires_in)
            if isinstance(signed_res, dict) and "signedUrl" in signed_res:
                return signed_res["signedUrl"]
            return str(signed_res)
        except Exception:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"

    def delete_file(self, bucket: str, file_path: str) -> bool:
        try:
            self.client.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            logger.error(f"Storage delete error: {e}")
            return False
