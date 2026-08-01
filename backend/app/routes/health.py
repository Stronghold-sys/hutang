from fastapi import APIRouter
from app.schemas.common import APIResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=APIResponse)
async def health_check():
    return APIResponse(
        success=True,
        message="Backend Utang Piutang API aktif dan berjalan",
        data={"status": "healthy"}
    )
