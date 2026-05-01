from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Staff(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Specializations (list of service IDs)
    service_ids = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="staff_members")
    bookings = relationship("Booking", back_populates="staff")

    def __repr__(self):
        return f"<Staff {self.name}>"
