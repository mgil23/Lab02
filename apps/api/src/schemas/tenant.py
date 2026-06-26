# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class TenantCreate(BaseModel):
    name: str
    slug: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]{2,63}$", v):
            raise ValueError("Slug must be 2-63 lowercase alphanumeric characters or hyphens")
        return v


class TenantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    slug: str
    name: str
    plan: str
    subscription_status: str
    settings: dict
    created_at: datetime


class TenantUpdate(BaseModel):
    name: str | None = None
    settings: dict | None = None
