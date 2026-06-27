# SPDX-License-Identifier: AGPL-3.0-or-later
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from ..dependencies import DbDep, CurrentUser
from ..models.tenant import Tenant
from ..models.user import User
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest
from ..core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DbDep) -> TokenResponse:
    # Check slug uniqueness
    result = await db.execute(select(Tenant).where(Tenant.slug == body.tenant_slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tenant slug already taken")

    tenant = Tenant(slug=body.tenant_slug, name=body.tenant_name)
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.id,
        email=body.email,
        hashed_password=hash_password(body.password),
        role="admin",
    )
    db.add(user)
    await db.flush()
    await db.commit()

    access = create_access_token(str(user.id), str(tenant.id), user.role)
    refresh = create_refresh_token(str(user.id), str(tenant.id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/token", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbDep) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access = create_access_token(str(user.id), str(user.tenant_id), user.role)
    refresh = create_refresh_token(str(user.id), str(user.tenant_id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbDep) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    # Check blacklist
    jti = payload.get("jti")
    if jti:
        import redis.asyncio as aioredis
        from ..config import settings
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        try:
            if await r.get(f"token_blacklist:{jti}"):
                raise HTTPException(status_code=401, detail="Token has been revoked")
        finally:
            await r.aclose()

    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(str(user.id), str(user.tenant_id), user.role)
    new_refresh = create_refresh_token(str(user.id), str(user.tenant_id))
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, current_user: CurrentUser) -> None:
    """Revoke the provided refresh token by adding its JTI to the blacklist."""
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        return  # Already invalid — nothing to revoke

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti:
        return

    import time
    import redis.asyncio as aioredis
    from ..config import settings

    ttl = max(1, int((exp or 0) - time.time())) if exp else 86400
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await r.setex(f"token_blacklist:{jti}", ttl, "1")
    finally:
        await r.aclose()
