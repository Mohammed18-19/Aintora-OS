"""
Super Admin API — only accessible by platform owner (role: super_admin).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.dependencies import require_super_admin
from app.models.user import User
from app.models.tenant import Tenant
from app.models.booking import Booking
from app.models.customer import Customer
from app.services.booking_service import BookingService

router = APIRouter(prefix="/admin", tags=["Super Admin"])


@router.get("/tenants")
async def list_tenants(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Tenant)
    if search:
        query = query.where(
            Tenant.name.ilike(f"%{search}%") | Tenant.email.ilike(f"%{search}%")
        )
    if is_active is not None:
        query = query.where(Tenant.is_active == is_active)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    tenants = result.scalars().all()

    tenant_data = []
    for t in tenants:
        booking_count = (
            await db.execute(
                select(func.count(Booking.id)).where(Booking.tenant_id == t.id)
            )
        ).scalar()
        customer_count = (
            await db.execute(
                select(func.count(Customer.id)).where(Customer.tenant_id == t.id)
            )
        ).scalar()

        tenant_data.append({
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "email": t.email,
            "phone": t.phone,
            "business_type": t.business_type,
            "plan": t.plan,
            "is_active": t.is_active,
            "is_verified": t.is_verified,
            "bookings_count": booking_count,
            "customers_count": customer_count,
            "created_at": t.created_at.isoformat(),
        })

    return {"tenants": tenant_data, "total": total, "limit": limit, "offset": offset}


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: uuid.UUID,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    svc = BookingService(db)
    stats = await svc.get_stats(tenant.id)

    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "phone": tenant.phone,
        "address": tenant.address,
        "city": tenant.city,
        "country": tenant.country,
        "business_type": tenant.business_type,
        "plan": tenant.plan,
        "is_active": tenant.is_active,
        "is_verified": tenant.is_verified,
        "settings": tenant.settings,
        "booking_stats": stats,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
    }


@router.post("/tenants/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: uuid.UUID,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.is_active = True
    return {"status": "activated", "tenant": tenant.slug}


@router.post("/tenants/{tenant_id}/deactivate")
async def deactivate_tenant(
    tenant_id: uuid.UUID,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant.is_active = False
    return {"status": "deactivated", "tenant": tenant.slug}


@router.get("/stats/platform")
async def platform_stats(
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Global platform KPIs."""
    total_tenants = (await db.execute(select(func.count(Tenant.id)))).scalar()
    active_tenants = (await db.execute(select(func.count(Tenant.id)).where(Tenant.is_active == True))).scalar()
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar()
    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar()

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_bookings": total_bookings,
        "total_customers": total_customers,
    }
