from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class BusinessType(str, enum.Enum):
    salon = "salon"
    clinic = "clinic"
    spa = "spa"
    barbershop = "barbershop"
    dental = "dental"
    fitness = "fitness"
    other = "other"


class SubscriptionPlan(str, enum.Enum):
    free = "free"
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class Tenant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    # Plain String columns — no SAEnum
    business_type = Column(String(50), default="other")
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="MA")
    timezone = Column(String(50), default="Africa/Casablanca")
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(10), default="#1a1a2e")
    language = Column(String(10), default="fr")
    plan = Column(String(50), default="free")
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    settings = Column(JSONB, default=dict, nullable=True)

    users = relationship("User", back_populates="tenant", lazy="selectin")
    services = relationship("Service", back_populates="tenant", lazy="selectin")
    staff_members = relationship("Staff", back_populates="tenant")
    bookings = relationship("Booking", back_populates="tenant")
    business_hours = relationship("BusinessHours", back_populates="tenant", lazy="selectin")
    whatsapp_config = relationship("WhatsAppConfig", back_populates="tenant", uselist=False, lazy="selectin")
    customers = relationship("Customer", back_populates="tenant")
    notification_logs = relationship("NotificationLog", back_populates="tenant")

    def __repr__(self):
        return f"<Tenant {self.slug}>"