from typing import Dict, Any, Optional
from json import dumps, loads
from app.core.config import settings
from app.core.exceptions import AppException, UnauthorizedException, ValidationException
from app.core.logging import logger


from datetime import date, datetime
from decimal import Decimal


def json_serial(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


async def http_request(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[Any] = None, timeout: float = 15.0):
    try:
        from js import fetch, Headers, Object, Reflect
        
        js_headers = Headers.new()
        if headers:
            for k, v in headers.items():
                js_headers.append(str(k), str(v))
        
        opts = Object.new()
        Reflect.set(opts, "method", method)
        Reflect.set(opts, "headers", js_headers)
        if body is not None:
            body_str = dumps(body, default=json_serial) if not isinstance(body, str) else body
            Reflect.set(opts, "body", body_str)
            
        res = await fetch(url, opts)
        status = res.status
        text = await res.text()
        try:
            data = loads(text) if text else {}
        except Exception:
            data = {"raw": text}
        return status, data
    except Exception as fetch_err:
        print(f"JS fetch error: {fetch_err}")
        import httpx
        async with httpx.AsyncClient() as client:
            body_bytes = (dumps(body, default=json_serial) if not isinstance(body, str) else body).encode('utf-8') if body is not None else None
            res = await client.request(method, url, headers=headers, content=body_bytes, timeout=timeout)
            status = res.status_code
            try:
                data = res.json()
            except Exception:
                data = {"raw": res.text}
            return status, data






class AuthService:
    async def register(self, email: str, password: str, full_name: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
        url = f"{settings.SUPABASE_URL}/auth/v1/signup"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "email": email,
            "password": password,
            "data": {
                "full_name": full_name or email,
                "phone": phone or ""
            }
        }
        try:
            status, data = await http_request(url, method="POST", headers=headers, body=body)
            if status >= 400 or not isinstance(data, dict):
                err_msg = data.get("msg") or data.get("error_description") or data.get("message") if isinstance(data, dict) else "Registrasi gagal"
                raise ValidationException(f"Registrasi gagal: {err_msg}")
            
            user = data.get("user") or {}
            session = data.get("session")

            # Upsert profile to profiles table via Supabase REST API
            if user.get("id"):
                prof_url = f"{settings.SUPABASE_URL}/rest/v1/profiles"
                prof_headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
                prof_body = {
                    "id": user["id"],
                    "email": email,
                    "full_name": full_name or email,
                    "phone": phone or "",
                    "role": "user"
                }
                try:
                    await http_request(prof_url, method="POST", headers=prof_headers, body=prof_body)
                except Exception as pe:
                    logger.warning(f"Profile upsert warning: {pe}")

            return {
                "user": user,
                "session": session
            }
        except (ValidationException, UnauthorizedException):
            raise
        except Exception as e:
            logger.error(f"Auth sign_up error: {e}")
            raise ValidationException(f"Registrasi gagal: {str(e)}")

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "email": email,
            "password": password
        }
        try:
            status, data = await http_request(url, method="POST", headers=headers, body=body)
            if status >= 400 or not isinstance(data, dict):
                err_msg = ""
                if isinstance(data, dict):
                    err_msg = data.get("error_description") or data.get("msg") or data.get("message") or data.get("error") or str(data)
                else:
                    err_msg = str(data)
                if "Invalid login credentials" in str(err_msg) or "invalid_grant" in str(err_msg):
                    err_msg = "Email atau password salah. Silakan daftar jika belum membuat akun."
                raise UnauthorizedException(f"Login gagal ({status}): {err_msg}")

            
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            user_raw = data.get("user") or {}

            # Fetch profile
            user_id = user_raw.get("id")
            user_profile = {
                "id": user_id,
                "email": user_raw.get("email", email),
                "full_name": user_raw.get("user_metadata", {}).get("full_name") or email,
                "role": "user"
            }
            if user_id:
                prof_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=*"
                prof_headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY}"
                }
                try:
                    prof_status, prof_data = await http_request(prof_url, method="GET", headers=prof_headers)
                    if prof_status == 200 and isinstance(prof_data, list) and len(prof_data) > 0:
                        user_profile = prof_data[0]
                except Exception as pe:
                    logger.warning(f"Profile fetch warning: {pe}")

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_profile
            }
        except (ValidationException, UnauthorizedException):
            raise
        except Exception as e:
            logger.error(f"Auth sign_in error: {e}")
            raise UnauthorizedException(f"Login gagal: {str(e)}")

    async def logout(self, token: str) -> bool:
        return True

    async def forgot_password(self, email: str) -> bool:
        url = f"{settings.SUPABASE_URL}/auth/v1/recover"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        try:
            status, data = await http_request(url, method="POST", headers=headers, body={"email": email})
            if status >= 400:
                err_msg = data.get("msg") if isinstance(data, dict) else "Gagal mengirim email reset password"
                raise AppException(message=err_msg)
            return True
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Forgot password error: {e}")
            raise AppException(message=f"Gagal mengirim email reset password: {str(e)}")

    async def reset_password(self, access_token: str, new_password: str) -> bool:
        url = f"{settings.SUPABASE_URL}/auth/v1/user"
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        try:
            status, data = await http_request(url, method="PUT", headers=headers, body={"password": new_password})
            if status >= 400:
                err_msg = data.get("msg") if isinstance(data, dict) else "Reset password gagal"
                raise AppException(message=err_msg)
            return True
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Reset password error: {e}")
            raise AppException(message=f"Reset password gagal: {str(e)}")

    async def change_password(self, user_id: str, new_password: str) -> bool:
        url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}"
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        try:
            status, data = await http_request(url, method="PUT", headers=headers, body={"password": new_password})
            if status >= 400:
                err_msg = data.get("msg") if isinstance(data, dict) else "Ubah password gagal"
                raise AppException(message=err_msg)
            return True
        except AppException:
            raise
        except Exception as e:
            logger.error(f"Change password error: {e}")
            raise AppException(message=f"Ubah password gagal: {str(e)}")
