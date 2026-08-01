from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "Permintaan tidak dapat diproses",
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Akses ditolak. Token tidak valid atau kadaluwarsa"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code="UNAUTHORIZED"
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Anda tidak memiliki hak akses untuk tindakan ini"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            code="FORBIDDEN"
        )


class NotFoundException(AppException):
    def __init__(self, message: str = "Sumber daya tidak ditemukan"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            code="NOT_FOUND"
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Validasi data gagal", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            code="VALIDATION_ERROR",
            details=details
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Terjadi konflik data"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            code="CONFLICT"
        )
