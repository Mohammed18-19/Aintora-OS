"""
AvailabilityService — checks if a given time slot is available for booking.
"""
from datetime import datetime, date, time, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pytz

from app.models.booking import Booking, BookingStatus
from app.models.business_hours import BusinessHours
from app.models.tenant import Tenant


class AvailabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_available(
        self,
        tenant: Tenant,
        requested_dt: datetime,
        duration_minutes: int = 60,
        staff_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Returns (is_available, reason).
        reason is empty string if available.
        """
        tz = pytz.timezone(tenant.timezone or "Africa/Casablanca")
        local_dt = requested_dt.astimezone(tz)

        # 1. Check business hours
        day_of_week = local_dt.weekday()
        hours_result = await self.db.execute(
            select(BusinessHours).where(
                BusinessHours.tenant_id == tenant.id,
                BusinessHours.day_of_week == day_of_week,
            )
        )
        bh = hours_result.scalar_one_or_none()

        if bh:
            if not bh.is_open:
                return False, "closed_today"

            req_time = local_dt.time()
            if bh.opens_at and req_time < bh.opens_at:
                return False, "outside_hours"
            if bh.closes_at and req_time >= bh.closes_at:
                return False, "outside_hours"

            # Check break time
            if bh.break_starts_at and bh.break_ends_at:
                if bh.break_starts_at <= req_time <= bh.break_ends_at:
                    return False, "outside_hours"

        # 2. Check for conflicting bookings
        end_dt = requested_dt + timedelta(minutes=duration_minutes)
        query = select(Booking).where(
            Booking.tenant_id == tenant.id,
            Booking.status.in_(["pending", "confirmed"]),
            Booking.scheduled_at < end_dt,
            Booking.ends_at > requested_dt,
        )
        if staff_id:
            from app.models.staff import Staff
            import uuid
            query = query.where(Booking.staff_id == uuid.UUID(staff_id))

        result = await self.db.execute(query)
        conflicts = result.scalars().all()
        if conflicts:
            return False, "slot_unavailable"

        return True, ""

    async def get_available_slots(
        self,
        tenant: Tenant,
        target_date: date,
        duration_minutes: int = 60,
    ) -> list[str]:
        """Return list of available HH:MM slots for a given date."""
        tz = pytz.timezone(tenant.timezone or "Africa/Casablanca")
        day_of_week = target_date.weekday()

        hours_result = await self.db.execute(
            select(BusinessHours).where(
                BusinessHours.tenant_id == tenant.id,
                BusinessHours.day_of_week == day_of_week,
            )
        )
        bh = hours_result.scalar_one_or_none()

        if not bh or not bh.is_open:
            return []

        opens = bh.opens_at or time(9, 0)
        closes = bh.closes_at or time(19, 0)

        slots = []
        current = datetime.combine(target_date, opens)
        end = datetime.combine(target_date, closes)

        while current + timedelta(minutes=duration_minutes) <= end:
            dt_aware = tz.localize(current)
            available, _ = await self.is_available(tenant, dt_aware, duration_minutes)
            if available:
                slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)  # 30-min grid

        return slots
