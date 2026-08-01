from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from app.schemas.common import APIResponse, MetaData, dump_model
from app.schemas.contact import ContactCreateRequest, ContactUpdateRequest
from app.services.contact import ContactService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])
contact_service = ContactService()


@router.get("", response_model=APIResponse)
async def list_contacts(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    result = await contact_service.get_contacts(
        user_id=current_user["id"],
        search=search,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total_pages = (result["total"] + limit - 1) // limit if limit > 0 else 1
    return APIResponse(
        success=True,
        message="Daftar kontak berhasil diambil",
        data=result["items"],
        meta=MetaData(
            page=page,
            limit=limit,
            total_items=result["total"],
            total_pages=total_pages
        )
    )


@router.post("", response_model=APIResponse)
async def create_contact(
    req: ContactCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    contact = await contact_service.create_contact(
        user_id=current_user["id"],
        name=req.name,
        phone=req.phone,
        email=req.email,
        address=req.address,
        notes=req.notes
    )
    return APIResponse(
        success=True,
        message="Kontak baru berhasil ditambahkan",
        data=contact
    )


@router.get("/{contact_id}", response_model=APIResponse)
async def get_contact(
    contact_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    contact = await contact_service.get_contact_by_id(contact_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Detail kontak berhasil diambil",
        data=contact
    )


@router.patch("/{contact_id}", response_model=APIResponse)
async def update_contact(
    contact_id: str,
    req: ContactUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = await contact_service.update_contact(
        contact_id=contact_id,
        user_id=current_user["id"],
        data=dump_model(req, exclude_unset=True)
    )
    return APIResponse(
        success=True,
        message="Kontak berhasil diperbarui",
        data=updated
    )
