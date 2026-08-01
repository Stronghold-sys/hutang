from typing import Dict, Any, Optional
from fastapi import Depends, Header
from app.core.security import verify_supabase_jwt
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.dependencies.db import get_supabase_admin_client


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    if not authorization:
        raise UnauthorizedException("Header Authorization tidak ditemukan")

    payload = await verify_supabase_jwt(authorization)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Identifier pengguna (sub) tidak valid")

    # Fetch user profile from DB or construct profile dict from payload
    profile = {
        "id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "user"),
        "full_name": payload.get("user_metadata", {}).get("full_name", payload.get("email", "")),
        "phone": payload.get("user_metadata", {}).get("phone", ""),
        "avatar_url": payload.get("user_metadata", {}).get("avatar_url", "")
    }

    try:
        from urllib.parse import quote
        from app.services.auth import http_request
        from app.core.config import settings
        url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{quote(str(user_id))}"
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
        }
        status, data = await http_request(url, method="GET", headers=headers, timeout=5.0)
        if status == 200 and isinstance(data, list) and len(data) > 0:
            db_profile = data[0]
            profile.update(db_profile)
    except Exception:
        # Fallback if DB is mock or initial creation hasn't completed
        pass

    return profile


def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise ForbiddenException(f"Peran '{user_role}' tidak memiliki izin untuk akses ini")
        return current_user
    return role_checker
