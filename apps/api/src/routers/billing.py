# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from ..config import settings
from ..dependencies import CurrentUser, DbDep, TenantDep
from ..models.tenant import Tenant
from ..models.usage_record import UsageRecord

stripe.api_key = settings.stripe_secret_key

# Tenant-scoped billing routes
router = APIRouter(prefix="/{tenant_slug}/billing", tags=["billing"])

# Stripe webhook — no tenant prefix (Stripe posts to fixed URL)
webhook_router = APIRouter(tags=["billing"])


@router.get("/info")
async def get_billing_info(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> dict:
    from datetime import datetime, UTC
    from ..core.rls import tenant_context

    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with tenant_context(db, tenant.id):
        pages_result = await db.execute(
            select(func.coalesce(func.sum(UsageRecord.quantity), 0))
            .where(
                UsageRecord.tenant_id == tenant.id,
                UsageRecord.metric == "pages_processed",
                UsageRecord.recorded_at >= month_start,
            )
        )
    pages_used = int(pages_result.scalar_one())

    limits: dict[str, int] = {"free": 100, "starter": 500, "professional": 3000, "enterprise": 999_999}
    pages_limit = limits.get(tenant.plan, 100)

    return {
        "plan": tenant.plan,
        "subscription_status": tenant.subscription_status,
        "pages_used_this_month": pages_used,
        "pages_limit": pages_limit,
    }


@router.post("/portal")
async def create_billing_portal(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> dict:
    if not tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found for this tenant")
    session = stripe.billing_portal.Session.create(
        customer=tenant.stripe_customer_id,
        return_url=f"{settings.frontend_url}/{tenant_slug}/billing",
    )
    return {"url": session.url}


@router.post("/checkout")
async def create_checkout_session(
    tenant_slug: str,
    price_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> dict:
    allowed = {settings.stripe_price_starter, settings.stripe_price_professional}
    if price_id not in allowed:
        raise HTTPException(status_code=400, detail="Invalid price ID")

    customer_id = tenant.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"tenant_id": str(tenant.id), "tenant_slug": tenant.slug},
        )
        customer_id = customer.id
        tenant.stripe_customer_id = customer_id
        await db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}/{tenant_slug}/billing?success=true",
        cancel_url=f"{settings.frontend_url}/{tenant_slug}/billing?canceled=true",
    )
    return {"url": session.url}


@webhook_router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: DbDep) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    obj = event["data"]["object"]
    match event["type"]:
        case "customer.subscription.updated":
            await _handle_subscription_updated(db, obj)
        case "customer.subscription.deleted":
            await _handle_subscription_deleted(db, obj)
        case "invoice.payment_failed":
            await _handle_payment_failed(db, obj)
        case "invoice.payment_succeeded":
            await _handle_payment_succeeded(db, obj)

    await db.commit()
    return {"received": True}


async def _handle_subscription_updated(db: object, sub: dict) -> None:
    result = await db.execute(  # type: ignore[union-attr]
        select(Tenant).where(Tenant.stripe_subscription_id == sub["id"])
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return
    tenant.subscription_status = sub["status"]
    tenant.stripe_subscription_id = sub["id"]
    plan_map = {
        settings.stripe_price_starter: "starter",
        settings.stripe_price_professional: "professional",
    }
    price_id = sub["items"]["data"][0]["price"]["id"]
    tenant.plan = plan_map.get(price_id, tenant.plan)


async def _handle_subscription_deleted(db: object, sub: dict) -> None:
    result = await db.execute(  # type: ignore[union-attr]
        select(Tenant).where(Tenant.stripe_subscription_id == sub["id"])
    )
    tenant = result.scalar_one_or_none()
    if tenant:
        tenant.subscription_status = "canceled"


async def _handle_payment_failed(db: object, invoice: dict) -> None:
    result = await db.execute(  # type: ignore[union-attr]
        select(Tenant).where(Tenant.stripe_customer_id == invoice["customer"])
    )
    tenant = result.scalar_one_or_none()
    if tenant:
        tenant.subscription_status = "past_due"


async def _handle_payment_succeeded(db: object, invoice: dict) -> None:
    result = await db.execute(  # type: ignore[union-attr]
        select(Tenant).where(Tenant.stripe_customer_id == invoice["customer"])
    )
    tenant = result.scalar_one_or_none()
    if tenant:
        tenant.subscription_status = "active"
