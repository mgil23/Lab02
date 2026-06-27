# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from datetime import datetime, UTC
import redis.asyncio as aioredis


async def emit_progress(
    redis: aioredis.Redis,
    tenant_id: str,
    document_id: str,
    stage: str,
    status: str,
    *,
    error: str | None = None,
    extra: dict | None = None,
) -> None:
    channel = f"pipeline:{tenant_id}:{document_id}"
    payload = {
        "type": "stage_progress",
        "stage": stage,
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        **({"error": error} if error else {}),
        **(extra or {}),
    }
    await redis.publish(channel, json.dumps(payload))


async def emit_field_updated(
    redis: aioredis.Redis,
    tenant_id: str,
    document_id: str,
    subdocument_id: str,
    field_id: str,
) -> None:
    channel = f"pipeline:{tenant_id}:{document_id}"
    payload = {
        "type": "field_updated",
        "subdocument_id": subdocument_id,
        "field_id": field_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    await redis.publish(channel, json.dumps(payload))
