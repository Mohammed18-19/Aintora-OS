from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class WhatsAppConfig(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "whatsapp_configs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Meta Cloud API credentials
    phone_number_id = Column(String(100), nullable=False)
    access_token = Column(Text, nullable=False)  # Should be encrypted in prod
    app_id = Column(String(100), nullable=True)
    waba_id = Column(String(100), nullable=True)  # WhatsApp Business Account ID

    # The business WhatsApp number (for sending notifications TO owner)
    owner_whatsapp = Column(String(30), nullable=True)

    # Webhook verify token (unique per tenant)
    verify_token = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Webhook verified by Meta

    # Message customization
    welcome_message = Column(Text, nullable=True)
    away_message = Column(Text, nullable=True)
    custom_templates = Column(JSONB, default=dict)

    # Relationships
    tenant = relationship("Tenant", back_populates="whatsapp_config")

    def __repr__(self):
        return f"<WhatsAppConfig tenant={self.tenant_id}>"
