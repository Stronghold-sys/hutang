from typing import Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from app.schemas.common import APIResponse, MetaData, dump_model
from app.schemas.debt import DebtCreateRequest, DebtUpdateRequest
from app.services.debt import DebtService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/debts", tags=["Debts"])
debt_service = DebtService()


@router.get("", response_model=APIResponse)
async def list_debts(
    search: Optional[str] = Query(None),
    debt_type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    due_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    result = await debt_service.get_debts(
        user_id=current_user["id"],
        search=search,
        debt_type=debt_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        due_status=due_status,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total_pages = (result["total"] + limit - 1) // limit if limit > 0 else 1
    return APIResponse(
        success=True,
        message="Daftar catatan utang/piutang berhasil diambil",
        data=result["items"],
        meta=MetaData(
            page=page,
            limit=limit,
            total_items=result["total"],
            total_pages=total_pages
        )
    )


@router.post("", response_model=APIResponse)
async def create_debt(
    req: DebtCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    debt = await debt_service.create_debt(
        user_id=current_user["id"],
        payload=dump_model(req)
    )
    return APIResponse(
        success=True,
        message="Catatan utang/piutang berhasil dibuat",
        data=debt
    )


@router.get("/{debt_id}", response_model=APIResponse)
async def get_debt(
    debt_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    debt = await debt_service.get_debt_by_id(debt_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Detail utang/piutang berhasil diambil",
        data=debt
    )


@router.patch("/{debt_id}", response_model=APIResponse)
async def update_debt(
    debt_id: str,
    req: DebtUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    updated = await debt_service.update_debt(
        debt_id=debt_id,
        user_id=current_user["id"],
        payload=dump_model(req, exclude_unset=True)
    )
    return APIResponse(
        success=True,
        message="Catatan utang/piutang berhasil diperbarui",
        data=updated
    )


@router.delete("/{debt_id}", response_model=APIResponse)
async def delete_debt(
    debt_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    await debt_service.delete_debt(debt_id, current_user["id"])
    return APIResponse(
        success=True,
        message="Catatan utang/piutang berhasil dihapus"
    )
