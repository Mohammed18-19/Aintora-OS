from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Customer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # WhatsApp identity
    whatsapp_number = Column(String(30), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)

    # Preferred language detected from messages
    preferred_language = Column(String(10), default="fr")

    # Stats
    total_bookings = Column(Integer, default=0)
    cancelled_bookings = Column(Integer, default=0)

    # State machine for conversation
    conversation_state = Column(String(50), default="idle")
    conversation_context = Column(JSONB, default=dict)

    is_blocked = Column(Boolean, default=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="customers")
    bookings = relationship("Booking", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.whatsapp_number}>"
