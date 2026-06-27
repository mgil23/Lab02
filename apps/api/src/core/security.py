# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import hmac
import secrets
from datetime import datetime, UTC, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta
        or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, tenant_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def generate_api_key() -> tuple[str, str]:
    """Returns (plain_key, key_hash). Store only the hash."""
    plain = f"oidp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(plain.encode()).hexdigest()
    return plain, key_hash


def hash_api_key(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def generate_webhook_secret() -> tuple[str, str]:
    """Returns (plain_secret, hashed_secret)."""
    plain = secrets.token_hex(32)
    hashed = hashlib.sha256(plain.encode()).hexdigest()
    return plain, hashed


def sign_webhook_payload(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
