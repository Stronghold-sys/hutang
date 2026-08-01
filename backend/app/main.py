from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import logger
from app.core.rate_limit import limiter
from app.core.exceptions import AppException
from app.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)

from app.routes import (
    health,
    auth,
    profile,
    contacts,
    debts,
    payments,
    evidences,
    reminders,
    notifications,
    dashboard,
    reports
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API untuk Aplikasi Catatan Utang Piutang dengan Supabase Integration",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Slowapi Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS is handled at the Cloudflare Worker edge level (worker.py)

# Routers
api_v1_prefix = "/api/v1"
app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(profile.router, prefix=api_v1_prefix)
app.include_router(contacts.router, prefix=api_v1_prefix)
app.include_router(debts.router, prefix=api_v1_prefix)
app.include_router(payments.router, prefix=api_v1_prefix)
app.include_router(evidences.router, prefix=api_v1_prefix)
app.include_router(reminders.router, prefix=api_v1_prefix)
app.include_router(notifications.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(reports.router, prefix=api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Aplikasi {settings.APP_NAME} berjalan pada lingkungan {settings.APP_ENV}")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs"
    }
