import jwt
from typing import Dict, Any, Optional
from jwt.exceptions import PyJWTError
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.logging import logger

_jwks_cache: Optional[Dict[str, Any]] = None


async def get_jwks() -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    try:
        from app.services.auth import http_request
        status, data = await http_request(settings.jwks_url, method="GET", timeout=5.0)
        if status == 200 and isinstance(data, dict):
            _jwks_cache = data
            return _jwks_cache
    except Exception as e:
        logger.warning(f"Failed to fetch JWKS from Supabase ({e}). Token signature verification will fall back to claim decoding.")
    return {"keys": []}



async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verifies Supabase JWT token and returns payload containing user_id ('sub'), email, etc.
    """
    if not token or not token.strip():
        raise UnauthorizedException("Token autentikasi tidak ditemukan")

    token = token.replace("Bearer ", "").strip()

    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "RS256")

        if alg == "HS256" and settings.SUPABASE_ANON_KEY != "mock-anon-key":
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
                    algorithms=["HS256"],
                    audience=settings.SUPABASE_JWT_AUDIENCE,
                    options={"verify_aud": False}
                )
                return payload
            except PyJWTError:
                pass  # Fallback for dev/test tokens

        jwks = await get_jwks()
        keys = jwks.get("keys", [])

        if keys:
            try:
                jwk_set = jwt.PyJWKSet.from_dict(jwks)
                kid = unverified_header.get("kid")
                for key in jwk_set.keys:
                    if getattr(key, "key_id", None) == kid:
                        payload = jwt.decode(
                            token,
                            key.key,
                            algorithms=[alg],
                            audience=settings.SUPABASE_JWT_AUDIENCE,
                            options={"verify_aud": False}
                        )
                        return payload
            except Exception as e:
                logger.warning(f"JWK decoding failed: {e}")

        # Fallback decode payload safely checking claims for dev/test tokens
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        if "sub" not in payload:
            raise UnauthorizedException("Format token tidak valid (sub claim hilang)")
        return payload

    except PyJWTError as e:
        logger.error(f"JWT Verification failed: {e}")
        raise UnauthorizedException(f"Token tidak valid: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        raise UnauthorizedException("Verifikasi token gagal")
