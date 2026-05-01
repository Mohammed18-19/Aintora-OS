from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_from_user
from app.models.user import User
from app.models.tenant import Tenant
from app.models.booking import Booking, BookingStatus
from app.services.booking_service import BookingService
from app.whatsapp.client import WhatsAppClient
from app.i18n import t

router = APIRouter(prefix="/bookings", tags=["Bookings"])


class BookingActionRequest(BaseModel):
    reason: Optional[str] = ""


class RescheduleRequest(BaseModel):
    new_datetime: datetime


@router.get("/")
async def list_bookings(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    status_enum = status if status else None
    bookings = await svc.list_for_tenant(tenant.id, status_enum, limit, offset)

    return {
        "bookings": [
            {
                "id": str(b.id),
                "booking_ref": b.booking_ref,
                "status": b.status,
                "scheduled_at": b.scheduled_at.isoformat() if b.scheduled_at else None,
                "service": b.service.name if b.service else None,
                "customer_number": b.customer.whatsapp_number if b.customer else None,
                "customer_name": b.customer.name if b.customer else None,
                "created_at": b.created_at.isoformat(),
            }
            for b in bookings
        ],
        "total": len(bookings),
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def booking_stats(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    return await svc.get_stats(tenant.id)


@router.get("/{booking_id}")
async def get_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.service),
            selectinload(Booking.customer),
            selectinload(Booking.staff),
        )
        .where(Booking.id == booking_id, Booking.tenant_id == tenant.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "id": str(booking.id),
        "booking_ref": booking.booking_ref,
        "status": booking.status,
        "scheduled_at": booking.scheduled_at.isoformat() if booking.scheduled_at else None,
        "ends_at": booking.ends_at.isoformat() if booking.ends_at else None,
        "service": {
            "id": str(booking.service.id),
            "name": booking.service.name,
        } if booking.service else None,
        "customer": {
            "number": booking.customer.whatsapp_number,
            "name": booking.customer.name,
            "language": booking.customer.preferred_language,
        } if booking.customer else None,
        "staff": {"id": str(booking.staff.id), "name": booking.staff.name} if booking.staff else None,
        "customer_notes": booking.customer_notes,
        "owner_notes": booking.owner_notes,
        "raw_message": booking.raw_message,
        "created_at": booking.created_at.isoformat(),
    }


@router.post("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    booking = await svc.confirm(booking_id, tenant.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Notify customer
    await _notify_customer_status(booking, tenant, "booking_confirmed")

    return {"status": "confirmed", "booking_ref": booking.booking_ref}


@router.post("/{booking_id}/reject")
async def reject_booking(
    booking_id: uuid.UUID,
    body: BookingActionRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    booking = await svc.reject(booking_id, tenant.id, body.reason)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await _notify_customer_status(booking, tenant, "booking_rejected")

    return {"status": "rejected", "booking_ref": booking.booking_ref}


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    booking = await svc.cancel(booking_id, tenant.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    await _notify_customer_status(booking, tenant, "booking_cancelled")
    return {"status": "cancelled", "booking_ref": booking.booking_ref}


@router.post("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: uuid.UUID,
    body: RescheduleRequest,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_tenant_from_user),
    db: AsyncSession = Depends(get_db),
):
    svc = BookingService(db)
    booking = await svc.reschedule(booking_id, tenant.id, body.new_datetime)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "status": "rescheduled",
        "booking_ref": booking.booking_ref,
        "new_time": booking.scheduled_at.isoformat(),
    }


async def _notify_customer_status(booking: Booking, tenant: Tenant, message_key: str):
    """Send WhatsApp confirmation/rejection to the customer."""
    if not tenant.whatsapp_config or not booking.customer:
        return

    client = WhatsAppClient(
        tenant.whatsapp_config.phone_number_id,
        tenant.whatsapp_config.access_token,
    )
    lang = booking.customer.preferred_language or "fr"

    await client.send_text(
        booking.customer.whatsapp_number,
        t(
            message_key, lang,
            service=booking.service.name if booking.service else "",
            date=booking.scheduled_at.strftime("%d/%m/%Y") if booking.scheduled_at else "",
            time=booking.scheduled_at.strftime("%H:%M") if booking.scheduled_at else "",
            booking_ref=booking.booking_ref,
        ),
    )
