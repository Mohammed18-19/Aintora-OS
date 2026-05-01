from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Service(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "services"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Duration in minutes
    duration_minutes = Column(Integer, default=60, nullable=False)

    # Price in MAD (or local currency)
    price = Column(Numeric(10, 2), default=0)
    currency = Column(String(5), default="MAD")

    # Category (e.g. "hair", "nails", "massage")
    category = Column(String(100), nullable=True)

    # Multilingual names (stored as JSON: {"ar": "...", "fr": "...", "en": "..."})
    name_translations = Column(JSONB, default=dict)

    # Aliases used in NLP parsing (e.g. ["coupe", "haircut", "تسريحة"])
    nlp_aliases = Column(JSONB, default=list)

    # Require specific staff?
    requires_staff = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)

    # Relationships
    tenant = relationship("Tenant", back_populates="services")
    bookings = relationship("Booking", back_populates="service")

    def __repr__(self):
        return f"<Service {self.name}>"
