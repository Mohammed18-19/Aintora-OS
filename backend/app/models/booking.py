from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    cancelled = "cancelled"
    completed = "completed"
    rescheduled = "rescheduled"
    no_show = "no_show"


class BookingSource(str, enum.Enum):
    whatsapp = "whatsapp"
    dashboard = "dashboard"
    api = "api"


class Booking(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)

    booking_ref = Column(String(20), unique=True, nullable=False, index=True)
    # Plain String — no SAEnum
    status = Column(String(50), default="pending", nullable=False, index=True)
    source = Column(String(50), default="whatsapp")

    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(String(10), default="60")
    ends_at = Column(DateTime(timezone=True), nullable=True)

    customer_notes = Column(Text, nullable=True)
    owner_notes = Column(Text, nullable=True)
    raw_message = Column(Text, nullable=True)

    original_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    reschedule_count = Column(String(5), default="0")

    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    meta = Column(JSONB, default=dict)

    tenant = relationship("Tenant", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")

    def __repr__(self):
        return f"<Booking {self.booking_ref} [{self.status}]>"