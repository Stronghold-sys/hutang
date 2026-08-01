from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppException
from app.core.logging import logger


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error": {
                "code": exc.code,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        field = ".".join([str(loc) for loc in err["loc"] if loc != "body"])
        errors[field] = err.get("msg")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validasi data gagal",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": errors
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Terjadi kesalahan internal server",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "details": {}
            }
        }
    )
