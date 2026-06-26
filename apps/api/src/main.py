# SPDX-License-Identifier: AGPL-3.0-or-later
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .config import settings
from .core.telemetry import setup_telemetry, prometheus_app
from .core.middleware import (
    TenantMiddleware,
    RateLimitMiddleware,
    MetricsMiddleware,
    SecurityHeadersMiddleware,
)
from .routers import auth, documents, extraction, document_types, billing, api_keys, storage, playground, ws
from .routers.billing import webhook_router
from .database import engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    setup_telemetry(settings.otel_exporter_otlp_endpoint, settings.otel_service_name)
    yield
    await engine.dispose()


app = FastAPI(
    title="OpenIDP SaaS API",
    version="1.0.0",
    description="World-class open-source Intelligent Document Processing platform",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)

# Middleware (order matters — last added = outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(extraction.router, prefix="/api/v1")
app.include_router(document_types.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")  # Stripe webhook at fixed URL
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(storage.router, prefix="/api/v1")
app.include_router(playground.router, prefix="/api/v1")
app.include_router(ws.router)

# Prometheus metrics endpoint
app.mount("/metrics", prometheus_app)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "openidp-api", "version": "1.0.0"}
