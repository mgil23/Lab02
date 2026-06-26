# OpenIDP SaaS

**World-class open-source Intelligent Document Processing platform** — AGPL-3.0

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

OpenIDP SaaS is a production-grade, self-hostable IDP platform comparable to ABBYY Vantage and UiPath Document Understanding, built entirely on open-source technology.

## Key Features

- **Multi-document PDF splitting** — Automatic boundary detection with full traceability
- **P95 < 60 s** end-to-end for 15-page mixed PDFs
- **Strong multi-tenancy** — PostgreSQL RLS, tenant-prefixed storage, rate limiting
- **AWS Strands Agents** — Structured extraction with explainability (bbox + reasoning)
- **Premium review workspace** — Bidirectional PDF↔field sync, inline table editing
- **Low-code document type builder** — Visual field schema + validation rule editor
- **Full SaaS billing** — Stripe subscriptions + metered usage
- **Enterprise-grade observability** — OpenTelemetry + Prometheus + Grafana

## Quick Start (Local Development)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/openidp-saas
cd openidp-saas
cp .env.example .env  # fill in your values

# 2. Start all services
docker compose -f infra/docker/docker-compose.dev.yml up

# 3. Run database migrations (in another terminal)
cd apps/api
uv run alembic upgrade head

# 4. Open the app
open http://localhost:3000
```

## Architecture

```
Browser ──► Next.js 15 ──► FastAPI 0.115 ──► PostgreSQL 16 (RLS)
                                │              Redis 7 (queue)
                            ARQ Workers        MinIO (storage)
                                │
                        PaddleOCR ONNX ──► AWS Strands Agents
```

See [`docs/architecture/`](docs/architecture/) for C4 diagrams and pipeline documentation.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15.3, Tailwind 4, shadcn/ui, TanStack Table v8, PDF.js + Konva |
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0, Pydantic v2, ARQ |
| Processing | PaddleOCR 3.0 (ONNX Runtime), PyMuPDF |
| Intelligence | AWS Strands Agents (Bedrock), LiteLLM fallback |
| Storage | PostgreSQL 16, Redis 7, MinIO |
| Infra | Docker, Kubernetes, Helm, OpenTelemetry, Prometheus, Grafana |
| Billing | Stripe (subscriptions + metered usage) |

## Performance (P95 targets)

| Stage | Budget | Notes |
|-------|--------|-------|
| Ingest + thumbnails | ≤ 3s | PyMuPDF + async MinIO upload |
| Preprocess + layout | ≤ 8s | PP-Structure ONNX |
| Classify + split | ≤ 6s | Multi-signal boundary detection |
| OCR (parallel) | ≤ 15s | PaddleOCR ONNX, ProcessPoolExecutor |
| Extraction + validation | ≤ 18s | Strands Agents, parallel per subdoc |
| Persist + events | ≤ 5s | Bulk insert + WebSocket fan-out |
| **Total** | **≤ 55s** | |

## Deployment

- **Docker Compose**: `infra/docker/docker-compose.dev.yml`
- **Kubernetes + Helm**: `infra/helm/openidp/`
- See [`docs/deployment/`](docs/deployment/) for detailed guides

## License

AGPL-3.0 — see [LICENSE](LICENSE)