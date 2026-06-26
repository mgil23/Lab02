# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import hmac
import json
import time
from datetime import datetime, UTC
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.webhook import Webhook, WebhookDelivery
from ..core.rls import tenant_context
import uuid


class WebhookService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def deliver_event(
        self,
        tenant_id: uuid.UUID,
        event: str,
        payload: dict,
    ) -> None:
        async with tenant_context(self._db, tenant_id):
            result = await self._db.execute(
                select(Webhook).where(
                    Webhook.tenant_id == tenant_id,
                    Webhook.is_active == True,  # noqa: E712
                    Webhook.events.contains([event]),
                )
            )
            webhooks = result.scalars().all()

        for webhook in webhooks:
            await self._send_with_retry(webhook, event, payload)

    async def _send_with_retry(
        self,
        webhook: Webhook,
        event: str,
        payload: dict,
        max_attempts: int = 5,
    ) -> None:
        payload_bytes = json.dumps(payload, default=str).encode()
        signature = hmac.new(
            webhook.secret_hash.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()

        for attempt in range(1, max_attempts + 1):
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event=event,
                payload=payload,
                attempt_number=attempt,
                created_at=datetime.now(UTC),
            )
            self._db.add(delivery)
            await self._db.flush()

            start = time.perf_counter()
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        webhook.url,
                        content=payload_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "X-OpenIDP-Signature": f"sha256={signature}",
                            "X-OpenIDP-Event": event,
                        },
                    )
                duration_ms = int((time.perf_counter() - start) * 1000)
                delivery.response_status = response.status_code
                delivery.response_body = response.text[:500]
                delivery.duration_ms = duration_ms
                delivery.delivered_at = datetime.now(UTC)

                if response.is_success:
                    await self._db.commit()
                    return
            except Exception as e:
                delivery.response_body = str(e)[:500]
                delivery.duration_ms = int((time.perf_counter() - start) * 1000)

            await self._db.commit()
            if attempt < max_attempts:
                import asyncio
                await asyncio.sleep(2 ** attempt)
