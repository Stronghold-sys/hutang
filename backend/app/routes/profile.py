from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File
from app.schemas.common import APIResponse, dump_model
from app.schemas.profile import ProfileUpdateRequest
from app.services.profile import ProfileService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])
profile_service = ProfileService()


@router.get("", response_model=APIResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    profile = await profile_service.get_profile(current_user["id"])
    return APIResponse(
        success=True,
        message="Profil pengguna berhasil diambil",
        data=profile
    )


@router.patch("", response_model=APIResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = await profile_service.update_profile(current_user["id"], dump_model(req, exclude_unset=True))
    return APIResponse(
        success=True,
        message="Profil berhasil diperbarui",
        data=updated
    )


@router.post("/avatar", response_model=APIResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    contents = await file.read()
    avatar_url = await profile_service.update_avatar(
        user_id=current_user["id"],
        file_bytes=contents,
        filename=file.filename or "avatar.png",
        content_type=file.content_type or "image/png"
    )
    return APIResponse(
        success=True,
        message="Foto profil berhasil diunggah",
        data={"avatar_url": avatar_url}
    )


@router.delete("/avatar", response_model=APIResponse)
async def delete_avatar(current_user: Dict[str, Any] = Depends(get_current_user)):
    await profile_service.delete_avatar(current_user["id"])
    return APIResponse(
        success=True,
        message="Foto profil berhasil dihapus"
    )


@router.delete("", response_model=APIResponse)
async def delete_account(current_user: Dict[str, Any] = Depends(get_current_user)):
    await profile_service.delete_account(current_user["id"])
    return APIResponse(
        success=True,
        message="Akun pengguna berhasil dihapus"
    )
