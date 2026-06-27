# SPDX-License-Identifier: AGPL-3.0-or-later
from arq import cron
from arq.connections import RedisSettings
import redis.asyncio as aioredis
from ..config import settings
from ..database import async_session_factory
from ..pipeline.orchestrator import run_pipeline
from ..core.telemetry import setup_telemetry


async def on_startup(ctx: dict) -> None:
    setup_telemetry(settings.otel_exporter_otlp_endpoint, settings.otel_service_name)
    ctx["redis"] = aioredis.from_url(settings.redis_url, decode_responses=True)
    ctx["db_factory"] = async_session_factory


async def on_shutdown(ctx: dict) -> None:
    await ctx["redis"].aclose()


async def _run_pipeline_task(ctx: dict, document_id: str, tenant_id: str) -> dict:
    """ARQ task wrapper — creates per-job DB session."""
    async with async_session_factory() as db:
        job_ctx = {**ctx, "db": db}
        return await run_pipeline(job_ctx, document_id, tenant_id)


async def report_usage_to_stripe(ctx: dict) -> dict:
    """Daily cron: report accumulated usage to Stripe Meter API."""
    import logging
    from datetime import datetime, UTC, timedelta
    from sqlalchemy import select
    from ..models.usage_record import UsageRecord
    from ..models.tenant import Tenant
    import stripe

    logger = logging.getLogger(__name__)
    stripe.api_key = settings.stripe_secret_key
    since = datetime.now(UTC) - timedelta(hours=24)

    async with async_session_factory() as db:
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.recorded_at >= since,
                UsageRecord.stripe_usage_record_id == None,  # noqa: E711
            )
        )
        records = result.scalars().all()

        # Pre-load tenant stripe_customer_ids to avoid N+1 queries
        tenant_ids = list({r.tenant_id for r in records})
        tenants_result = await db.execute(
            select(Tenant).where(Tenant.id.in_(tenant_ids))
        )
        tenant_map = {t.id: t for t in tenants_result.scalars().all()}

        reported = 0
        for record in records:
            tenant = tenant_map.get(record.tenant_id)
            if not tenant or not tenant.stripe_customer_id:
                continue
            try:
                stripe_event = stripe.billing.MeterEvent.create(
                    event_name=record.metric,
                    payload={
                        "stripe_customer_id": tenant.stripe_customer_id,
                        "value": str(int(record.quantity)),
                    },
                    timestamp=int(record.recorded_at.timestamp()),
                )
                record.stripe_usage_record_id = stripe_event.id
                reported += 1
            except Exception as exc:
                logger.warning("Stripe meter event failed for record %s: %s", record.id, exc)

        await db.commit()

    return {"reported": reported}


class WorkerSettings:
    functions = [_run_pipeline_task]
    cron_jobs = [
        cron(report_usage_to_stripe, hour=2, minute=0)
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    queue_read_limit = 10
    max_jobs = 20
    job_timeout = 120
    on_startup = on_startup
    on_shutdown = on_shutdown
    queue_name = "pipeline"
