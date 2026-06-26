# SPDX-License-Identifier: AGPL-3.0-or-later
import stripe
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from ..dependencies import DbDep, CurrentUser, TenantDep
from ..models.tenant import Tenant
from ..config import settings

router = APIRouter(prefix="/billing", tags=["billing"])
stripe.api_key = settings.stripe_secret_key


@router.post("/{tenant_slug}/portal")
async def create_billing_portal(
    tenant_slug: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> dict:
    if not tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")
    session = stripe.billing_portal.Session.create(
        customer=tenant.stripe_customer_id,
        return_url=f"{settings.frontend_url}/{tenant_slug}/billing",
    )
    return {"url": session.url}


@router.post("/{tenant_slug}/checkout")
async def create_checkout_session(
    tenant_slug: str,
    price_id: str,
    db: DbDep,
    current_user: CurrentUser,
    tenant: TenantDep,
) -> dict:
    allowed_prices = {settings.stripe_price_starter, settings.stripe_price_professional}
    if price_id not in allowed_prices:
        raise HTTPException(status_code=400, detail="Invalid price")

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


@router.post("/webhook/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: DbDep) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError:  # type: ignore[attr-defined]
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    data = event["data"]["object"]
    event_type = event["type"]

    async with db.begin():
        if event_type == "customer.subscription.updated":
            await _handle_subscription_updated(db, data)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(db, data)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(db, data)
        elif event_type == "invoice.payment_succeeded":
            await _handle_payment_succeeded(db, data)

    return {"received": True}


async def _handle_subscription_updated(db: object, sub: dict) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession
    result = await db.execute(  # type: ignore[union-attr]
        select(Tenant).where(Tenant.stripe_subscription_id == sub["id"])
    )
    tenant = result.scalar_one_or_none()
    if tenant:
        tenant.subscription_status = sub["status"]
        plan_map = {
            settings.stripe_price_starter: "starter",
            settings.stripe_price_professional: "professional",
        }
        price_id = sub["items"]["data"][0]["price"]["id"]
        tenant.plan = plan_map.get(price_id, tenant.plan)
        tenant.stripe_subscription_id = sub["id"]


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
