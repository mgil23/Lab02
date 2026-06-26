# Configuration Reference

All configuration is handled via environment variables loaded from `.env` at startup.
Copy `.env.example` to `.env` and fill in the values described below.

For Docker Compose the variables are read directly from `.env` in the project root.
For Kubernetes, use the Helm `secrets.*` values or Kubernetes Secrets referenced in `values.yaml`.

---

## PostgreSQL

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `devpassword` | Password for the `openidp` database user (Docker Compose) |
| `DATABASE_URL` | `postgresql+asyncpg://openidp:changeme@localhost:5432/openidp` | Full asyncpg connection URL used by the API and workers |

**Production:** Use a managed database (AWS RDS, Cloud SQL) and provide the `DATABASE_URL` directly. Enable SSL: `postgresql+asyncpg://user:pass@host/db?ssl=require`

---

## Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (used for ARQ queue, rate limiting, pub/sub) |

**Production:** Use a managed Redis (ElastiCache, Upstash). For TLS: `rediss://...`

---

## MinIO / S3

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO host:port (without scheme) |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key (root user for local MinIO) |
| `MINIO_SECRET_KEY` | `minioadmin123` | Secret key |
| `MINIO_BUCKET` | `openidp-documents` | Bucket name (created automatically on first use) |
| `MINIO_SECURE` | `false` | Set `true` for HTTPS endpoints |

**Using AWS S3:** Set `MINIO_ENDPOINT` to `s3.amazonaws.com`, set `MINIO_SECURE=true`, and use IAM credentials.

---

## Authentication (JWT)

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | _(required)_ | 256-bit secret for signing JWTs. Generate: `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm. `RS256` is supported for key-pair rotation. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |

> **Security:** `JWT_SECRET` must be changed from the default before any production deployment. A compromised secret allows arbitrary token forgery.

---

## OCR Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_ENGINE_URL` | `http://localhost:8001` | Internal URL of the OCR microservice |

The OCR engine itself reads:

| Variable | Default | Description |
|----------|---------|-------------|
| `OCR_MODEL_DIR` | `/app/models` | Directory containing `det/`, `rec/`, `cls/` subdirectories |
| `USE_GPU` | `false` | Set `true` on GPU-enabled nodes (requires NVIDIA drivers + CUDA 12.1) |
| `ORT_INTRA_THREADS` | `4` | ONNX Runtime intra-op parallelism (set to physical CPU cores) |
| `ORT_INTER_THREADS` | `2` | ONNX Runtime inter-op parallelism |

---

## AWS Bedrock (Strands Agents)

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region where Bedrock is enabled |
| `AWS_ACCESS_KEY_ID` | _(required for extraction)_ | IAM access key with `bedrock:InvokeModel` permission |
| `AWS_SECRET_ACCESS_KEY` | _(required for extraction)_ | IAM secret key |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-6` | Model ID for extraction. Can be overridden to any Claude model available in your region. |

**Required IAM policy:**
```json
{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
  "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude*"
}
```

**If you don't have AWS credentials:** The system uses a graceful fallback — extraction will skip the LLM step and return field stubs that can be filled in manually via the review workspace.

---

## Stripe Billing

| Variable | Default | Description |
|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | `sk_test_placeholder` | Stripe API key (`sk_live_` in production) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_placeholder` | Webhook endpoint secret from the Stripe dashboard |
| `STRIPE_PRICE_STARTER` | — | Price ID of the Starter plan (`price_...`) |
| `STRIPE_PRICE_PROFESSIONAL` | — | Price ID of the Professional plan |

**Webhook endpoint:** Configure `https://your-domain.com/api/v1/webhook/stripe` in the Stripe dashboard with these events:
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`
- `invoice.payment_succeeded`

**If you don't need billing:** Leave the Stripe variables as placeholders. The billing endpoints will return errors but the rest of the platform functions normally.

---

## OpenTelemetry

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC exporter endpoint (OTel Collector) |
| `OTEL_SERVICE_NAME` | `openidp-api` | Service name shown in traces |

Disable telemetry by leaving the endpoint pointing at a non-existent host — the exporter will silently drop spans.

---

## Application

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` or `production`. Controls log verbosity, API docs visibility, debug middleware. |
| `DEBUG` | `true` | Enables `/api/docs` and `/api/redoc` Swagger UIs. Set `false` in production. |
| `LOG_LEVEL` | `INFO` | Python log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. Example: `https://app.mycompany.com` |
| `FRONTEND_URL` | `http://localhost:3000` | Used for Stripe redirect URLs. Must match the public URL of the web frontend. |

---

## Frontend environment variables

Frontend variables are set at **build time** (Next.js bakes them in). For Docker Compose they're set in the `web` service environment. For Kubernetes they're in `values.yaml` under `web.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Public URL of the FastAPI backend (called from the browser) |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket base URL (`ws://` for HTTP, `wss://` for HTTPS) |

---

## Rate limits

Rate limiting uses a Redis sliding-window counter per (IP, tenant). The defaults are hard-coded in `apps/api/src/core/middleware.py` and can be adjusted:

| Endpoint category | Default limit |
|-------------------|--------------|
| `/auth/*` | 20 req/min |
| `POST /documents` (upload) | 60 req/min |
| All other API routes | 300 req/min |
