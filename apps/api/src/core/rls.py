# SPDX-License-Identifier: AGPL-3.0-or-later
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def tenant_context(db: AsyncSession, tenant_id: UUID) -> AsyncGenerator[None, None]:
    """Set PostgreSQL RLS context for the current transaction."""
    await db.execute(
        text("SELECT set_config('app.tenant_id', :tid, TRUE)"),
        {"tid": str(tenant_id)},
    )
    yield
