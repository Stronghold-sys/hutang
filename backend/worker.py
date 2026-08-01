import os
import sys
from json import dumps, loads
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urlparse, parse_qs

vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
if os.path.exists(vendor_dir) and vendor_dir not in sys.path:
    sys.path.append(vendor_dir)

# Safe fallback for importlib.metadata in Pyodide environment
import importlib.metadata
try:
    _orig_version = importlib.metadata.version
    def _safe_version(package_name):
        try:
            return _orig_version(package_name)
        except Exception:
            if package_name == 'email-validator':
                return '2.1.0'
            if package_name == 'fastapi':
                return '0.110.0'
            return '1.0.0'
    importlib.metadata.version = _safe_version
except Exception:
    pass

try:
    import pyodide_http
    pyodide_http.patch_all()
except Exception as e:
    print(f"pyodide_http patch error: {e}")

from js import Response, Headers, Uint8Array

def json_serial(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _make_cors_headers(request_origin=None):
    """Build JS Headers with CORS fields, reflecting the request origin when possible."""
    js_headers = Headers.new()
    origin_value = request_origin if request_origin else "*"
    js_headers.append("Access-Control-Allow-Origin", origin_value)
    js_headers.append("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    js_headers.append("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, Origin, X-Requested-With")
    js_headers.append("Access-Control-Expose-Headers", "*")
    js_headers.append("Access-Control-Max-Age", "86400")
    if request_origin:
        js_headers.append("Vary", "Origin")
    return js_headers


async def get_current_user_from_request(request):
    auth_header = None
    try:
        for pair in request.headers:
            if pair[0].lower() == "authorization":
                auth_header = pair[1]
                break
    except Exception:
        pass

    if not auth_header:
        raise Exception("Header Authorization tidak ditemukan")

    from app.core.security import verify_supabase_jwt
    payload = await verify_supabase_jwt(auth_header)
    user_id = payload.get("sub")
    if not user_id:
        raise Exception("Identifier pengguna (sub) tidak valid")
    return {
        "id": user_id,
        "email": payload.get("email", ""),
        "role": payload.get("role", "user"),
        "full_name": payload.get("user_metadata", {}).get("full_name", payload.get("email", "")),
        "phone": payload.get("user_metadata", {}).get("phone", "")
    }


async def on_fetch(request, env):
    request_origin = None
    try:
        # Load Cloudflare environment variables and secrets into os.environ
        try:
            if hasattr(env, "to_py"):
                env_dict = env.to_py()
            else:
                env_dict = dict(env)
            for key, val in env_dict.items():
                if isinstance(val, str):
                    os.environ[key] = val
        except Exception as e:
            print(f"env load error: {e}")

        # Extract request origin for CORS reflection
        try:
            for pair in request.headers:
                if pair[0].lower() == "origin":
                    request_origin = pair[1]
                    break
        except Exception:
            pass

        # Handle CORS preflight (OPTIONS) at the edge
        if request.method == "OPTIONS":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "text/plain")
            cors_headers.append("Content-Length", "0")
            return Response.new("", status=204, headers=cors_headers)

        url = urlparse(request.url)
        path = url.path or "/"
        method = request.method
        raw_query = parse_qs(url.query)
        query_params = {k: v[0] for k, v in raw_query.items() if v}

        # 1. Health check
        if path in ["/api/v1/health", "/health", "/"]:
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            return Response.new(
                '{"success":true,"message":"Backend Utang Piutang API aktif dan berjalan","data":{"status":"healthy"}}',
                status=200,
                headers=cors_headers
            )

        # 2. Auth (Login & Register)
        if path == "/api/v1/auth/login" and method == "POST":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                array_buffer = await request.arrayBuffer()
                body_bytes = bytes(Uint8Array.new(array_buffer))
                body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                from app.services.auth import AuthService
                svc = AuthService()
                res = await svc.login(body_json.get("email", ""), body_json.get("password", ""))
                return Response.new(
                    dumps({"success": True, "message": "Login berhasil", "data": res}, default=json_serial),
                    status=200, headers=cors_headers
                )
            except Exception as auth_err:
                err_msg = str(auth_err)
                status_code = 401 if "Login gagal" in err_msg or "Unauthorized" in err_msg else 400
                return Response.new(dumps({"success": False, "message": err_msg}), status=status_code, headers=cors_headers)

        if path == "/api/v1/auth/register" and method == "POST":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                array_buffer = await request.arrayBuffer()
                body_bytes = bytes(Uint8Array.new(array_buffer))
                body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                from app.services.auth import AuthService
                svc = AuthService()
                res = await svc.register(
                    body_json.get("email", ""),
                    body_json.get("password", ""),
                    body_json.get("full_name"),
                    body_json.get("phone")
                )
                return Response.new(
                    dumps({"success": True, "message": "Registrasi akun berhasil.", "data": res}, default=json_serial),
                    status=200, headers=cors_headers
                )
            except Exception as auth_err:
                return Response.new(dumps({"success": False, "message": str(auth_err)}), status=400, headers=cors_headers)

        # 3. Dashboard
        if path.startswith("/api/v1/dashboard"):
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                from app.services.dashboard import DashboardService
                svc = DashboardService()
                if path == "/api/v1/dashboard/summary":
                    data = await svc.get_summary(user["id"])
                elif path == "/api/v1/dashboard/cash-flow":
                    data = await svc.get_cash_flow(user["id"])
                elif path == "/api/v1/dashboard/upcoming-due-dates":
                    data = await svc.get_upcoming_due_dates(user["id"])
                elif path == "/api/v1/dashboard/recent-activities":
                    data = await svc.get_recent_activities(user["id"])
                else:
                    data = await svc.get_summary(user["id"])
                return Response.new(
                    dumps({"success": True, "message": "Berhasil", "data": data}, default=json_serial),
                    status=200, headers=cors_headers
                )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # 4. Debts List & Create
        if path == "/api/v1/debts" and method == "GET":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                from app.services.debt import DebtService
                svc = DebtService()
                search = query_params.get("search")
                debt_type = query_params.get("type")
                status_filter = query_params.get("status")
                limit_val = int(query_params.get("limit", 50))
                page_val = int(query_params.get("page", 1))
                result = await svc.get_debts(
                    user_id=user["id"],
                    search=search,
                    debt_type=debt_type,
                    status=status_filter,
                    page=page_val,
                    limit=limit_val
                )
                items = result.get("items", []) if isinstance(result, dict) else result
                total = result.get("total", len(items)) if isinstance(result, dict) else len(items)
                total_pages = (total + limit_val - 1) // limit_val if limit_val > 0 else 1
                return Response.new(
                    dumps({
                        "success": True,
                        "message": "Daftar catatan utang/piutang berhasil diambil",
                        "data": items,
                        "meta": {"page": page_val, "limit": limit_val, "total_items": total, "total_pages": total_pages}
                    }, default=json_serial),
                    status=200, headers=cors_headers
                )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        if path == "/api/v1/debts" and method == "POST":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                array_buffer = await request.arrayBuffer()
                body_bytes = bytes(Uint8Array.new(array_buffer))
                body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                from app.services.debt import DebtService
                svc = DebtService()
                debt = await svc.create_debt(user_id=user["id"], payload=body_json)
                return Response.new(
                    dumps({"success": True, "message": "Catatan utang/piutang berhasil dibuat", "data": debt}, default=json_serial),
                    status=200, headers=cors_headers
                )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # 5. Debts item routes: /api/v1/debts/{debt_id} and /api/v1/debts/{debt_id}/payments
        if path.startswith("/api/v1/debts/"):
            parts = [p for p in path.split("/") if p]
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                debt_id = parts[3] if len(parts) >= 4 else None

                if len(parts) == 5 and parts[4] == "payments":
                    from app.services.payment import PaymentService
                    svc = PaymentService()
                    if method == "GET":
                        pays = await svc.get_debt_payments(debt_id, user["id"])
                        return Response.new(
                            dumps({"success": True, "message": "Riwayat pembayaran berhasil diambil", "data": pays}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "POST":
                        array_buffer = await request.arrayBuffer()
                        body_bytes = bytes(Uint8Array.new(array_buffer))
                        body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                        pay = await svc.create_payment(debt_id=debt_id, user_id=user["id"], payload=body_json)
                        return Response.new(
                            dumps({"success": True, "message": "Pembayaran berhasil dicatat", "data": pay}, default=json_serial),
                            status=200, headers=cors_headers
                        )

                elif len(parts) == 4:
                    from app.services.debt import DebtService
                    svc = DebtService()
                    if method == "GET":
                        debt = await svc.get_debt_by_id(debt_id, user["id"])
                        return Response.new(
                            dumps({"success": True, "message": "Detail utang/piutang berhasil diambil", "data": debt}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "PATCH":
                        array_buffer = await request.arrayBuffer()
                        body_bytes = bytes(Uint8Array.new(array_buffer))
                        body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                        updated = await svc.update_debt(debt_id=debt_id, user_id=user["id"], payload=body_json)
                        return Response.new(
                            dumps({"success": True, "message": "Catatan utang/piutang berhasil diperbarui", "data": updated}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "DELETE":
                        await svc.delete_debt(debt_id=debt_id, user_id=user["id"])
                        return Response.new(
                            dumps({"success": True, "message": "Catatan utang/piutang berhasil dihapus"}, default=json_serial),
                            status=200, headers=cors_headers
                        )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # 6. Contacts
        if path.startswith("/api/v1/contacts"):
            parts = [p for p in path.split("/") if p]
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                from app.services.contact import ContactService
                svc = ContactService()

                if len(parts) == 3: # /api/v1/contacts
                    if method == "GET":
                        search = query_params.get("search")
                        result = await svc.get_contacts(user_id=user["id"], search=search)
                        items = result.get("items", []) if isinstance(result, dict) else result
                        total = result.get("total", len(items)) if isinstance(result, dict) else len(items)
                        return Response.new(
                            dumps({"success": True, "message": "Daftar kontak berhasil diambil", "data": items, "meta": {"page": 1, "limit": 50, "total_items": total, "total_pages": 1}}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "POST":
                        array_buffer = await request.arrayBuffer()
                        body_bytes = bytes(Uint8Array.new(array_buffer))
                        body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                        contact = await svc.create_contact(
                            user_id=user["id"],
                            name=body_json.get("name"),
                            phone=body_json.get("phone"),
                            email=body_json.get("email"),
                            address=body_json.get("address"),
                            notes=body_json.get("notes")
                        )
                        return Response.new(
                            dumps({"success": True, "message": "Kontak baru berhasil ditambahkan", "data": contact}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                elif len(parts) == 4: # /api/v1/contacts/{contact_id}
                    contact_id = parts[3]
                    if method == "GET":
                        c = await svc.get_contact_by_id(contact_id, user["id"])
                        return Response.new(
                            dumps({"success": True, "message": "Detail kontak berhasil diambil", "data": c}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "PATCH":
                        array_buffer = await request.arrayBuffer()
                        body_bytes = bytes(Uint8Array.new(array_buffer))
                        body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                        updated = await svc.update_contact(contact_id=contact_id, user_id=user["id"], data=body_json)
                        return Response.new(
                            dumps({"success": True, "message": "Kontak berhasil diperbarui", "data": updated}, default=json_serial),
                            status=200, headers=cors_headers
                        )
                    elif method == "DELETE":
                        await svc.delete_contact(contact_id=contact_id, user_id=user["id"])
                        return Response.new(
                            dumps({"success": True, "message": "Kontak berhasil dihapus"}, default=json_serial),
                            status=200, headers=cors_headers
                        )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # 7. Reports
        if path.startswith("/api/v1/reports"):
            cors_headers = _make_cors_headers(request_origin)
            try:
                user = await get_current_user_from_request(request)
                from app.services.report import ReportService
                from app.services.debt import DebtService
                svc = ReportService()
                debt_svc = DebtService()

                if path == "/api/v1/reports/summary":
                    cors_headers.append("Content-Type", "application/json")
                    data = await svc.get_summary(user["id"])
                    return Response.new(
                        dumps({"success": True, "message": "Ringkasan laporan berhasil diambil", "data": data}, default=json_serial),
                        status=200, headers=cors_headers
                    )
                elif path == "/api/v1/reports/debts":
                    cors_headers.append("Content-Type", "application/json")
                    res = await debt_svc.get_debts(user_id=user["id"], limit=1000)
                    items = res.get("items", []) if isinstance(res, dict) else res
                    return Response.new(
                        dumps({"success": True, "message": "Laporan utang/piutang berhasil diambil", "data": items}, default=json_serial),
                        status=200, headers=cors_headers
                    )
                elif path == "/api/v1/reports/export":
                    fmt = query_params.get("format", "xlsx")
                    content, media_type, filename = await svc.export_report(user["id"], fmt)
                    cors_headers.append("Content-Type", media_type)
                    cors_headers.append("Content-Disposition", f"attachment; filename={filename}")
                    if isinstance(content, bytes):
                        js_content = Uint8Array.new(len(content))
                        js_content.assign(content)
                    else:
                        js_content = str(content)
                    return Response.new(js_content, status=200, headers=cors_headers)
            except Exception as err:
                cors_headers.append("Content-Type", "application/json")
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # 8. Profile
        if path == "/api/v1/profile":
            cors_headers = _make_cors_headers(request_origin)
            cors_headers.append("Content-Type", "application/json")
            try:
                user = await get_current_user_from_request(request)
                from app.services.profile import ProfileService
                svc = ProfileService()
                if method == "GET":
                    prof = await svc.get_profile(user["id"])
                    return Response.new(
                        dumps({"success": True, "message": "Profil pengguna berhasil diambil", "data": prof}, default=json_serial),
                        status=200, headers=cors_headers
                    )
                elif method == "PATCH":
                    array_buffer = await request.arrayBuffer()
                    body_bytes = bytes(Uint8Array.new(array_buffer))
                    body_json = loads(body_bytes.decode('utf-8')) if body_bytes else {}
                    updated = await svc.update_profile(user_id=user["id"], payload=body_json)
                    return Response.new(
                        dumps({"success": True, "message": "Profil pengguna berhasil diperbarui", "data": updated}, default=json_serial),
                        status=200, headers=cors_headers
                    )
            except Exception as err:
                status_code = 401 if "Authorization" in str(err) or "token" in str(err).lower() else 400
                return Response.new(dumps({"success": False, "message": str(err)}), status=status_code, headers=cors_headers)

        # Fallback 404 Not Found
        cors_headers = _make_cors_headers(request_origin)
        cors_headers.append("Content-Type", "application/json")
        return Response.new(
            dumps({"success": False, "message": f"Endpoint not found: {path}"}),
            status=404,
            headers=cors_headers
        )

    except Exception as fatal_exc:
        cors_headers = _make_cors_headers(request_origin)
        cors_headers.append("Content-Type", "application/json")
        return Response.new(
            f'{{"success":false,"message":"Unhandled Worker Error: {str(fatal_exc)}"}}',
            status=500,
            headers=cors_headers
        )


