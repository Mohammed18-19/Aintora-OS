from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_from_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.service import Service
from app.models.staff import Staff
from app.models.business_hours import BusinessHours
from app.models.whatsapp_config import WhatsAppConfig

router = APIRouter(tags=["Tenant Settings"])


# ─── Services ─────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = 60
    price: float = 0
    currency: str = "MAD"
    category: Optional[str] = None
    name_translations: dict = Field(default_factory=dict)
    nlp_aliases: List[str] = Field(default_factory=list)

class ServiceUpdate(ServiceCreate):
    is_active: Optional[bool] = None


services_router = APIRouter(prefix="/services", tags=["Services"])

@services_router.get("/")
async def list_services(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
):
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "duration_minutes": s.duration_minutes,
            "price": float(s.price),
            "currency": s.currency,
            "category": s.category,
            "is_active": s.is_active,
            "nlp_aliases": s.nlp_aliases,
            "name_translations": s.name_translations,
        }
        for s in (tenant.services or [])
    ]

@services_router.post("/", status_code=201)
async def create_service(
    body: ServiceCreate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    service = Service(tenant_id=tenant.id, **body.model_dump())
    db.add(service)
    await db.flush()
    return {"id": str(service.id), "name": service.name}

@services_router.put("/{service_id}")
async def update_service(
    service_id: uuid.UUID,
    body: ServiceUpdate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Service).where(Service.id == service_id, Service.tenant_id == tenant.id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(service, k, v)
    return {"status": "updated"}

@services_router.delete("/{service_id}")
async def delete_service(
    service_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Service).where(Service.id == service_id, Service.tenant_id == tenant.id))
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.is_active = False  # Soft delete
    return {"status": "deactivated"}


# ─── Staff ────────────────────────────────────────────────────────────────────

class StaffCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    service_ids: List[str] = Field(default_factory=list)


staff_router = APIRouter(prefix="/staff", tags=["Staff"])

@staff_router.get("/")
async def list_staff(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Staff).where(Staff.tenant_id == tenant.id, Staff.is_active == True))
    staff = result.scalars().all()
    return [{"id": str(s.id), "name": s.name, "phone": s.phone, "email": s.email} for s in staff]

@staff_router.post("/", status_code=201)
async def create_staff(
    body: StaffCreate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    staff = Staff(tenant_id=tenant.id, **body.model_dump())
    db.add(staff)
    await db.flush()
    return {"id": str(staff.id), "name": staff.name}


# ─── Business Hours ───────────────────────────────────────────────────────────

class HoursUpdate(BaseModel):
    day_of_week: int
    is_open: bool
    opens_at: Optional[str] = None
    closes_at: Optional[str] = None


hours_router = APIRouter(prefix="/business-hours", tags=["Business Hours"])

@hours_router.get("/")
async def get_hours(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
):
    return [
        {
            "day_of_week": h.day_of_week,
            "day_name": BusinessHours.DAY_NAMES.get(h.day_of_week),
            "is_open": h.is_open,
            "opens_at": h.opens_at.strftime("%H:%M") if h.opens_at else None,
            "closes_at": h.closes_at.strftime("%H:%M") if h.closes_at else None,
        }
        for h in (tenant.business_hours or [])
    ]

@hours_router.put("/")
async def update_hours(
    body: List[HoursUpdate],
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import time
    for update in body:
        result = await db.execute(
            select(BusinessHours).where(
                BusinessHours.tenant_id == tenant.id,
                BusinessHours.day_of_week == update.day_of_week
            )
        )
        bh = result.scalar_one_or_none()
        if not bh:
            bh = BusinessHours(tenant_id=tenant.id, day_of_week=update.day_of_week)
            db.add(bh)
        bh.is_open = update.is_open
        if update.opens_at:
            h, m = map(int, update.opens_at.split(":"))
            bh.opens_at = time(h, m)
        if update.closes_at:
            h, m = map(int, update.closes_at.split(":"))
            bh.closes_at = time(h, m)
    return {"status": "updated"}


# ─── WhatsApp Config ──────────────────────────────────────────────────────────

class WhatsAppConfigUpdate(BaseModel):
    phone_number_id: str
    access_token: str
    owner_whatsapp: Optional[str] = None
    waba_id: Optional[str] = None
    welcome_message: Optional[str] = None
    away_message: Optional[str] = None


wa_router = APIRouter(prefix="/whatsapp-config", tags=["WhatsApp Config"])

@wa_router.get("/")
async def get_wa_config(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
):
    wac = tenant.whatsapp_config
    if not wac:
        return {"configured": False}
    return {
        "configured": True,
        "phone_number_id": wac.phone_number_id,
        "owner_whatsapp": wac.owner_whatsapp,
        "is_active": wac.is_active,
        "webhook_url": f"/api/v1/webhook/{tenant.slug}",
    }

@wa_router.post("/")
async def save_wa_config(
    body: WhatsAppConfigUpdate,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    import secrets
    result = await db.execute(select(WhatsAppConfig).where(WhatsAppConfig.tenant_id == tenant.id))
    wac = result.scalar_one_or_none()
    if not wac:
        wac = WhatsAppConfig(
            tenant_id=tenant.id,
            verify_token=secrets.token_urlsafe(16),
        )
        db.add(wac)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(wac, k, v)
    await db.flush()
    return {
        "status": "saved",
        "verify_token": wac.verify_token,
        "webhook_url": f"/api/v1/webhook/{tenant.slug}",
    }
