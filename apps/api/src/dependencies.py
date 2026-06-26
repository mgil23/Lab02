# SPDX-License-Identifier: AGPL-3.0-or-later
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .models.user import User
from .models.tenant import Tenant
from .models.api_key import ApiKey
from .core.security import decode_token, hash_api_key
from .core.rls import tenant_context

bearer_scheme = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_from_jwt(
    credentials: HTTPAuthorizationCredentials | None,
    db: AsyncSession,
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user_from_api_key(
    api_key_header: str,
    db: AsyncSession,
) -> User:
    key_hash = hash_api_key(api_key_header)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    user_result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    db: DbDep,
) -> User:
    if credentials and credentials.scheme.lower() == "bearer":
        if credentials.credentials.startswith("oidp_"):
            return await get_current_user_from_api_key(credentials.credentials, db)
        return await get_current_user_from_jwt(credentials, db)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_tenant(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if current_user.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return tenant


TenantDep = Annotated[Tenant, Depends(get_tenant)]


def require_role(*roles: str):
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role!r} not allowed. Required: {roles}",
            )
        return current_user

    return Depends(_check)
