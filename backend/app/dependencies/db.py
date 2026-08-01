from typing import Optional, Any
from app.core.config import settings
from app.core.logging import logger

_supabase_anon: Optional[Any] = None
_supabase_admin: Optional[Any] = None


def get_supabase_client() -> Any:
    global _supabase_anon
    if _supabase_anon is None:
        from supabase import create_client
        _supabase_anon = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _supabase_anon


def get_supabase_admin_client() -> Any:
    global _supabase_admin
    if _supabase_admin is None:
        from supabase import create_client
        _supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin
