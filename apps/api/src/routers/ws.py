# SPDX-License-Identifier: AGPL-3.0-or-later
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from ..config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{tenant_id}/{document_id}")
async def websocket_pipeline_events(
    websocket: WebSocket,
    tenant_id: str,
    document_id: str,
) -> None:
    await websocket.accept()
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    channel = f"pipeline:{tenant_id}:{document_id}"

    async with redis.pubsub() as pubsub:
        await pubsub.subscribe(channel)
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)
                if message and message["type"] == "message":
                    await websocket.send_text(message["data"])
                else:
                    # Send keepalive ping
                    await websocket.send_json({"type": "ping"})
        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await redis.aclose()
