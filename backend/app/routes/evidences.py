from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.schemas.common import APIResponse
from app.services.evidence import EvidenceService
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["Evidences"])
evidence_service = EvidenceService()


@router.get("/debts/{debt_id}/evidences", response_model=APIResponse)
async def list_evidences(
    debt_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    evidences = await evidence_service.get_evidences(debt_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Daftar bukti transaksi berhasil diambil",
        data=evidences
    )


@router.post("/debts/{debt_id}/evidences", response_model=APIResponse)
async def upload_evidence(
    debt_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    contents = await file.read()
    evidence = await evidence_service.upload_evidence(
        debt_id=debt_id,
        user_id=current_user["id"],
        file_bytes=contents,
        filename=file.filename or "evidence.png",
        content_type=file.content_type or "image/png",
        description=description
    )
    return APIResponse(
        success=True,
        message="Bukti transaksi berhasil diunggah",
        data=evidence
    )


@router.delete("/evidences/{evidence_id}", response_model=APIResponse)
async def delete_evidence(
    evidence_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await evidence_service.delete_evidence(evidence_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Bukti transaksi berhasil dihapus"
    )
