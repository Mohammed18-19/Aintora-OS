from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.tenant import Tenant

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def get_tenant_from_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no associated tenant")
    result = await db.execute(
        select(Tenant)
        .options(
            selectinload(Tenant.services),
            selectinload(Tenant.whatsapp_config),
            selectinload(Tenant.business_hours),
        )
        .where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant account is deactivated")
    return tenant
