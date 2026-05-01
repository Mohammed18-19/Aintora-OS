from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import uuid

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    business_name: str
    business_type: str = "other"
    phone: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    tenant_id: str | None = None
    user_id: str


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(
        subject=user.id,
        role=user.role,
        tenant_id=user.tenant_id,
    )
    return TokenResponse(
        access_token=token,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        user_id=str(user.id),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new business owner (creates tenant + user)."""
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create slug
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", payload.business_name.lower()).strip("-")
    slug_base = slug
    counter = 1
    while True:
        existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    # Create tenant
    tenant = Tenant(
        name=payload.business_name,
        slug=slug,
        email=payload.email.lower(),
        phone=payload.phone,
        business_type=payload.business_type,
    )
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=UserRole.owner,
    )
    db.add(user)
    await db.flush()

    # Seed default business hours (Mon-Sat 9:00-19:00)
    from app.models.business_hours import BusinessHours
    from datetime import time
    for day in range(6):  # Mon-Sat
        db.add(BusinessHours(
            tenant_id=tenant.id,
            day_of_week=day,
            is_open=True,
            opens_at=time(9, 0),
            closes_at=time(19, 0),
        ))
    # Sunday closed
    db.add(BusinessHours(
        tenant_id=tenant.id,
        day_of_week=6,
        is_open=False,
    ))

    token = create_access_token(
        subject=user.id,
        role=user.role,
        tenant_id=tenant.id,
    )
    return TokenResponse(
        access_token=token,
        role=user.role,
        tenant_id=str(tenant.id),
        user_id=str(user.id),
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None,
    }
