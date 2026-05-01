from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    owner = "owner"
    staff = "staff"
    viewer = "viewer"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    # Plain String — no SAEnum, no PostgreSQL ENUM type created
    role = Column(String(50), nullable=False, default="owner")
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False)

    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"