from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.whatsapp import router as webhook_router
from app.api.v1.endpoints.bookings import router as bookings_router
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.settings import (
    services_router,
    staff_router,
    hours_router,
    wa_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(webhook_router)
api_router.include_router(bookings_router)
api_router.include_router(admin_router)
api_router.include_router(services_router)
api_router.include_router(staff_router)
api_router.include_router(hours_router)
api_router.include_router(wa_router)
