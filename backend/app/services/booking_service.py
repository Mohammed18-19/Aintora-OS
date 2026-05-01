"""
BookingService — central business logic for all booking operations.
"""
import uuid
import random
from datetime import datetime, date, time, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import structlog
import pytz

from app.models.booking import Booking, BookingStatus, BookingSource
from app.models.customer import Customer
from app.models.service import Service
from app.models.tenant import Tenant

logger = structlog.get_logger()


class BookingService:
    async def _generate_booking_ref(self, tenant_slug: str) -> str:
        """Generate a unique booking ref like BK-2024-001234."""
        year = datetime.now().year
        while True:
            ref = f"BK-{year}-{random.randint(100000, 999999)}"
            result = await self.db.execute(select(Booking).where(Booking.booking_ref == ref))
            if not result.scalar_one_or_none():
                return ref

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_whatsapp(
        self,
        tenant: Tenant,
        customer: Customer,
        service_id: Optional[str],
        date_str: Optional[str],
        time_str: Optional[str],
        raw_message: str = "",
        staff_id: Optional[str] = None,
    ) -> Booking:
        """Create a booking from a WhatsApp conversation."""
        tz = pytz.timezone(tenant.timezone or "Africa/Casablanca")

        # Build scheduled_at datetime
        try:
            d = date.fromisoformat(date_str) if date_str else date.today()
            t_obj = time.fromisoformat(time_str + ":00") if time_str and ":" in time_str else time(10, 0)
            naive_dt = datetime.combine(d, t_obj)
            scheduled_at = tz.localize(naive_dt)
        except Exception:
            scheduled_at = datetime.now(tz)

        service_id_uuid = None
        if service_id:
            try:
                service_id_uuid = uuid.UUID(service_id)
            except (ValueError, TypeError):
                service_id_uuid = None

        booking = Booking(
            tenant_id=tenant.id,
            customer_id=customer.id,
            service_id=service_id_uuid,
            staff_id=uuid.UUID(staff_id) if staff_id else None,
            booking_ref=await self._generate_booking_ref(tenant.slug),
            status="pending",
            source="whatsapp",
            scheduled_at=scheduled_at,
            raw_message=raw_message,
        )

        # Set ends_at based on service duration
        if service_id_uuid:
            result = await self.db.execute(select(Service).where(Service.id == service_id_uuid))
            service = result.scalar_one_or_none()
            if service:
                from datetime import timedelta
                booking.ends_at = scheduled_at + timedelta(minutes=service.duration_minutes)
                booking.duration_minutes = str(service.duration_minutes)

        self.db.add(booking)
        await self.db.flush()

        # Update customer booking count
        customer.total_bookings = (customer.total_bookings or 0) + 1

        logger.info("booking_created", ref=booking.booking_ref, tenant=tenant.slug)
        return booking

    async def confirm(self, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Booking]:
        booking = await self._get(booking_id, tenant_id)
        if booking and booking.status == "pending":
            booking.status = "confirmed"
            await self.db.flush()
        return booking

    async def reject(self, booking_id: uuid.UUID, tenant_id: uuid.UUID, reason: str = "") -> Optional[Booking]:
        booking = await self._get(booking_id, tenant_id)
        if booking and booking.status == "pending":
            booking.status = "rejected"
            booking.owner_notes = reason
            await self.db.flush()
        return booking

    async def cancel(self, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Booking]:
        booking = await self._get(booking_id, tenant_id)
        if booking and booking.status not in ("completed", "cancelled"):
            booking.status = "cancelled"
            await self.db.flush()
        return booking

    async def cancel_by_ref(self, ref: str, tenant_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Booking).where(
                Booking.booking_ref == ref.upper(),
                Booking.tenant_id == tenant_id,
            )
        )
        booking = result.scalar_one_or_none()
        if booking:
            booking.status = "cancelled"
            await self.db.flush()
            return True
        return False

    async def reschedule(
        self,
        booking_id: uuid.UUID,
        tenant_id: uuid.UUID,
        new_dt: datetime,
    ) -> Optional[Booking]:
        booking = await self._get(booking_id, tenant_id)
        if booking:
            booking.original_scheduled_at = booking.scheduled_at
            booking.scheduled_at = new_dt
            booking.status = "rescheduled"
            booking.reschedule_count = str(int(booking.reschedule_count or "0") + 1)
            await self.db.flush()
        return booking

    async def get_by_ref(self, ref: str, tenant_id: uuid.UUID) -> Optional[Booking]:
        result = await self.db.execute(
            select(Booking).options(
                selectinload(Booking.service),
                selectinload(Booking.customer),
                selectinload(Booking.staff),
            ).where(
                Booking.booking_ref == ref.upper(),
                Booking.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self,
        tenant_id: uuid.UUID,
        status: Optional[BookingStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        query = select(Booking).options(
            selectinload(Booking.service),
            selectinload(Booking.customer),
        ).where(Booking.tenant_id == tenant_id)
        if status:
            query = query.where(Booking.status == status)
        query = query.order_by(Booking.scheduled_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_stats(self, tenant_id: uuid.UUID) -> dict:
        """Return booking statistics for a tenant."""
        result = await self.db.execute(
            select(
                func.count(Booking.id).label("total"),
                Booking.status,
            )
            .where(Booking.tenant_id == tenant_id)
            .group_by(Booking.status)
        )
        rows = result.all()
        stats = {row.status: row.total for row in rows}
        stats["total"] = sum(stats.values())
        return stats

    async def _get(self, booking_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Booking]:
        result = await self.db.execute(
            select(Booking).options(
                selectinload(Booking.service),
                selectinload(Booking.customer),
                selectinload(Booking.staff),
            ).where(
                Booking.id == booking_id,
                Booking.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()
