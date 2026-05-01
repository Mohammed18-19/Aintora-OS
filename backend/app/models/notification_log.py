from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class NotificationType(str, enum.Enum):
    booking_confirmation = "booking_confirmation"
    booking_rejection = "booking_rejection"
    booking_reminder = "booking_reminder"
    booking_cancellation = "booking_cancellation"
    owner_alert = "owner_alert"
    welcome = "welcome"
    away = "away"
    custom = "custom"


class NotificationStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"
    pending = "pending"
    delivered = "delivered"
    read = "read"


class NotificationLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notification_logs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)

    # Plain String — no SAEnum
    notification_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")

    recipient_number = Column(String(30), nullable=False)
    message_body = Column(Text, nullable=True)
    whatsapp_message_id = Column(String(100), nullable=True)
    meta_response = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="notification_logs")

    def __repr__(self):
        return f"<NotificationLog {self.notification_type} → {self.recipient_number}>"