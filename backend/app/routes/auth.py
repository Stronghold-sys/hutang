from typing import Dict, Any
from fastapi import APIRouter, Depends, Header
from app.schemas.common import APIResponse
from app.schemas.auth import (
    RegisterRequest, LoginRequest, ForgotPasswordRequest,
    ResetPasswordRequest, ChangePasswordRequest
)
from app.services.auth import AuthService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/register", response_model=APIResponse)
async def register(req: RegisterRequest):
    result = await auth_service.register(req.email, req.password, req.full_name, req.phone)
    return APIResponse(
        success=True,
        message="Registrasi akun berhasil. Silakan cek email jika butuh verifikasi.",
        data=result
    )


@router.post("/login", response_model=APIResponse)
async def login(req: LoginRequest):
    result = await auth_service.login(req.email, req.password)
    return APIResponse(
        success=True,
        message="Login berhasil",
        data=result
    )


@router.post("/logout", response_model=APIResponse)
async def logout(authorization: str = Header(...)):
    await auth_service.logout(authorization)
    return APIResponse(
        success=True,
        message="Sesi berhasil ditutup"
    )


@router.get("/me", response_model=APIResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return APIResponse(
        success=True,
        message="Data pengguna berhasil diambil",
        data=current_user
    )


@router.post("/forgot-password", response_model=APIResponse)
async def forgot_password(req: ForgotPasswordRequest):
    await auth_service.forgot_password(req.email)
    return APIResponse(
        success=True,
        message="Tautan reset password telah dikirim ke email Anda"
    )


@router.post("/reset-password", response_model=APIResponse)
async def reset_password(req: ResetPasswordRequest):
    await auth_service.reset_password(req.access_token, req.new_password)
    return APIResponse(
        success=True,
        message="Password berhasil diperbarui"
    )


@router.post("/change-password", response_model=APIResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await auth_service.change_password(current_user["id"], req.new_password)
    return APIResponse(
        success=True,
        message="Password berhasil diubah"
    )
