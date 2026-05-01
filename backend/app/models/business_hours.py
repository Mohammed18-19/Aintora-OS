from sqlalchemy import Column, Boolean, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class BusinessHours(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "business_hours"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # 0 = Monday, 6 = Sunday
    day_of_week = Column(Integer, nullable=False)

    is_open = Column(Boolean, default=True)
    opens_at = Column(Time, nullable=True)  # e.g. 09:00
    closes_at = Column(Time, nullable=True) # e.g. 19:00

    # Optional break time
    break_starts_at = Column(Time, nullable=True)
    break_ends_at = Column(Time, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="business_hours")

    DAY_NAMES = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday",
        3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"
    }

    def __repr__(self):
        return f"<BusinessHours {self.DAY_NAMES.get(self.day_of_week)} {'open' if self.is_open else 'closed'}>"
