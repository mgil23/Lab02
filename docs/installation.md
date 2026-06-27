# Installation Guide

This guide covers every step needed to run OpenIDP SaaS from source, both for local development and production.

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Docker | 24.0+ | With Docker Compose v2 (bundled) |
| Git | 2.40+ | |
| Python | 3.12+ | Only needed for native dev (not Docker) |
| Node.js | 20 LTS | Only needed for native dev (not Docker) |
| pnpm | 9+ | `npm install -g pnpm` |
| uv | 0.4+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| AWS account | — | Required for Strands Agents (Bedrock). Can be skipped — the app runs with a fallback mode. |
| Stripe account | — | Required for billing features. Can be skipped for dev. |

**Hardware minimum (development):**
- 4 CPU cores, 8 GB RAM
- 10 GB free disk space (Docker images + models)

**Hardware recommended (production, CPU OCR):**
- 8 cores, 16 GB RAM, 50 GB SSD
- For GPU-accelerated OCR: NVIDIA GPU with CUDA 12.1+, 8 GB VRAM

---

## 1. Clone and configure

```bash
git clone https://github.com/your-org/openidp-saas
cd openidp-saas

# Copy environment template and edit values
cp .env.example .env
```

Open `.env` and fill in at minimum:
- `JWT_SECRET` — generate with `openssl rand -hex 32`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — for Strands Agents extraction
- `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` — for billing (leave placeholders to skip)

See [configuration.md](./configuration.md) for a full description of every variable.

---

## 2. Download OCR models

The OCR engine requires PaddleOCR ONNX models (~350 MB total). They are **not bundled**
with the repository and must be downloaded once before first use.

### Option A — Docker volume (recommended for Docker Compose)

```bash
# Run the model downloader inside a temporary container that mounts
# the same named volume the ocr-engine service uses.
docker run --rm \
  -v openidp_ocr_models:/app/models \
  -v "$(pwd)/scripts:/scripts" \
  python:3.12-slim \
  bash /scripts/download_models.sh /app/models
```

The volume `openidp_ocr_models` persists between `docker compose up/down` cycles —
you only need to run this once per Docker environment.

### Option B — Local directory (for native / non-Docker dev)

```bash
bash scripts/download_models.sh packages/ocr-engine/models
```

Then point the OCR engine at the local path:
```bash
# In packages/ocr-engine, set OCR_MODEL_DIR before starting:
export OCR_MODEL_DIR=./models
uvicorn src.ocr_engine.main:app --port 8001
```

### Model files and sizes

| Model | Size | Purpose |
|-------|------|---------|
| `det/` PP-OCRv4 detection | ~8 MB | Text region detection |
| `rec/` PP-OCRv4 recognition | ~12 MB | Text recognition in detected regions |
| `cls/` orientation classifier | ~2 MB | Page orientation correction |

> **Offline/air-gapped environments:** Download the `.tar` files from
> `https://paddleocr.bj.bcebos.com/PP-OCRv4/english/` on a machine with internet
> access, transfer them, and extract manually:
> ```bash
> tar -xz -C packages/ocr-engine/models/det/ < en_PP-OCRv4_det_infer.tar
> tar -xz -C packages/ocr-engine/models/rec/ < en_PP-OCRv4_rec_infer.tar
> ```

---

## 3. Start all services (Docker Compose)

```bash
docker compose -f infra/docker/docker-compose.dev.yml up --build
```

This starts 9 services:

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL 16 database |
| `redis` | 6379 | Redis 7 queue + pub/sub |
| `minio` | 9000 / 9001 | Object storage (API / Console) |
| `api` | 8000 | FastAPI backend |
| `worker` | — | ARQ pipeline workers (×2 replicas) |
| `ocr-engine` | 8001 | PaddleOCR ONNX microservice |
| `web` | 3000 | Next.js frontend |
| `prometheus` | 9090 | Metrics collection |
| `grafana` | 3001 | Metrics dashboard (admin/admin) |

Wait until you see:
```
api        | INFO:     Application startup complete.
web        | ✓ Ready on http://localhost:3000
ocr-engine | INFO:     Application startup complete.
```

---

## 4. Run database migrations

```bash
# In a new terminal, with services running:
docker compose -f infra/docker/docker-compose.dev.yml exec api \
  uv run alembic upgrade head
```

This creates all 13 tables, enables Row-Level Security, and seeds the
`set_tenant_context()` stored function.

---

## 5. Verify the installation

```bash
# API health check
curl http://localhost:8000/api/health
# Expected: {"status":"ok","service":"openidp-api","version":"1.0.0"}

# OCR engine health check
curl http://localhost:8001/health
# Expected: {"status":"ok","service":"ocr-engine"}

# Open the frontend
open http://localhost:3000
```

---

## 6. Native development (without Docker)

For faster iteration you can run components natively. You still need Postgres,
Redis, and MinIO running — using Docker just for infrastructure is convenient:

```bash
# Start only infrastructure
docker compose -f infra/docker/docker-compose.dev.yml up postgres redis minio

# Backend
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --port 8000 --reload

# ARQ worker (separate terminal)
cd apps/api
uv run python -m src.workers.arq_worker

# OCR engine (separate terminal)
cd packages/ocr-engine
uv sync
OCR_MODEL_DIR=./models uv run uvicorn src.ocr_engine.main:app --port 8001

# Frontend (separate terminal)
cd apps/web
pnpm install
pnpm dev
```

---

## Next steps

- [Configuration reference](./configuration.md)
- [Usage guide](./usage.md)
- [Kubernetes / Helm deployment](./deployment/kubernetes.md)
- [Architecture overview](./architecture/overview.md)
