# Architecture Overview

## System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenIDP SaaS                             │
│   (AGPL-3.0, self-hostable enterprise IDP platform)         │
└──────────────────────────┬──────────────────────────────────┘
         ▲                  │                    ▲
  Document Reviewer    REST / WebSocket    Developer / Integrator
  (reviews extracted    (upload, query,     (API keys, webhooks,
   data via browser)     correct fields)     programmatic access)
         │                  │                    │
         └──────────────────┼────────────────────┘
                    External dependencies:
         ┌─────────────────┼────────────────────┐
         │                 │                    │
   AWS Bedrock       Stripe Billing        OIDC / SSO
  (claude-sonnet     (subscriptions +     (enterprise
  via Strands)        metered usage)       identity)
```

## Container Diagram (C4 Level 2)

```
Browser
  │
  ├─HTTP──► [Next.js 15 :3000]
  │            │ REST             ┌─────────────────────┐
  │            └──────────────►  │ FastAPI API :8000    │
  │                              │ (auth, routing, RLS) │
  │                              └──┬──────────┬────────┘
  │  WebSocket                      │          │
  └─WS─────────────────────────────┘          │
                                     ┌─────────▼──────────┐
                                     │  PostgreSQL 16       │
                                     │  (RLS multi-tenant) │
                                     └─────────────────────┘
                                     ┌─────────────────────┐
                             queue → │  Redis 7             │
                                     │  (ARQ + pub/sub)    │
                                     └──────────┬──────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │   ARQ Workers ×3     │
                                     │  (pipeline stages)   │
                                     └──────────┬──────────┘
                                                │
                          ┌─────────────────────┼──────────────────┐
                          │                     │                   │
              ┌───────────▼────────┐  ┌─────────▼──────┐  ┌───────▼────────┐
              │   MinIO / S3        │  │  OCR Engine     │  │ Strands Agents │
              │  (tenant-prefixed   │  │  :8001          │  │ (AWS Bedrock)  │
              │   object storage)   │  │  PaddleOCR ONNX │  │ claude-sonnet  │
              └────────────────────┘  └────────────────┘  └────────────────┘

[OTel Collector] → [Prometheus] → [Grafana]
```

## Processing Pipeline

Each uploaded PDF goes through 6 sequential stages (run by ARQ workers):

```
Upload PDF
    │
    ▼ ≤3s P95
[Stage 1: Ingest]
  PyMuPDF → page count + raw text per page
  Generate WebP thumbnails (one per page)
  Upload to MinIO: {tenant_id}/{year}/{month}/{doc_id}/original.pdf
  Create Document row; enqueue to ARQ pipeline queue
    │
    ▼ ≤8s P95
[Stage 2: Preprocess + Layout]
  PP-Structure (ONNX) per page
  → text blocks, tables, figures, headers with bounding boxes
  Store layout JSON in Redis (TTL 1h) + DB
    │
    ▼ ≤6s P95
[Stage 3: Classify + Split]
  Per-page TF-IDF classifier + layout features → doc type probabilities
  Multi-signal boundary detection:
    HARD (weight ≥ 0.85): blank separator page, "Page 1 of N" restart,
                           header entity change (Jaccard < 0.3)
    SOFT (weight 0.5–0.7): layout delta > 0.4, topic cosine < 0.3
  Boundary threshold: 0.55 (sum of signal weights)
  Group pages into SubDocuments with INT4RANGE page_range
  Extract sub-PDFs → MinIO per subdocument
    │
    ▼ ≤15s P95  (parallel across subdocuments)
[Stage 4: OCR]
  PaddleOCR ONNX (ProcessPoolExecutor, 4 workers, bypasses GIL)
  Merge with PyMuPDF native text (prefer native if confidence > 0.95)
  Table matrix extraction via PP-Structure
    │
    ▼ ≤18s P95  (parallel across subdocuments)
[Stage 5: Strands Agents Extraction + Validation]
  PII sanitization (Presidio) before any LLM call
  ExtractionAgent per subdocument:
    extract_fields @tool  → all schema fields (value, confidence, bbox, reasoning)
    validate_field @tool  → business rule checks
    resolve_ambiguity @tool → when confidence < 0.7
    flag_for_human_review @tool → unresolvable fields
  Restore PII tokens in results
  Persist ExtractedField rows with bbox + reasoning
    │
    ▼ ≤5s P95
[Stage 6: Persist + Events]
  Update Document / SubDocument status
  Record UsageRecord (pages_processed, llm_tokens)
  Fire webhooks (async, 5-attempt exponential backoff)
  Publish WebSocket event → all connected clients for this document
    │
    ▼
 COMPLETED  (total P95 ≤ 55s)
```

## Multi-Tenancy

Every tenant's data is isolated at three independent layers:

1. **Database — Row-Level Security (PostgreSQL RLS)**
   All tenant-scoped tables have `ENABLE ROW LEVEL SECURITY` plus a policy
   that checks `tenant_id = current_setting('app.tenant_id', TRUE)::UUID`.
   The `set_tenant_context()` SECURITY DEFINER function sets this value inside
   a transaction via `SET LOCAL` — safe for async connection pools (per-transaction,
   not per-connection).

2. **Object storage — tenant-prefixed keys**
   All MinIO/S3 objects are stored at `{tenant_id}/{year}/{month}/{doc_id}/...`.
   There are no bucket-level ACLs to misconfigure; the prefix is enforced in the
   `StorageService` class.

3. **Rate limiting — per-(IP, tenant) sliding window**
   Redis ZADD/ZCOUNT sliding window prevents one tenant's traffic from affecting
   others.

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| RLS isolation | `SET LOCAL app.tenant_id` | Transaction-local; safe for asyncpg pooling |
| OCR parallelism | `ProcessPoolExecutor` | Bypasses GIL for CPU-bound ONNX inference |
| AI determinism | `temperature=0.0` on Bedrock | Consistent structured extraction |
| WebSocket architecture | API → Redis Pub/Sub → WS | API stays fully stateless, horizontally scalable |
| SubDocument page tracking | `INT4RANGE` + GIST index | Efficient `@>` operator for page ownership queries |
| LLM calls | Strands Agents only when conf < 0.7 | Deterministic rules first = speed + cost control |
| Storage isolation | MinIO prefix `{tenant_id}/` | No ACL complexity; enforced in code |
| Schema per tenant | RLS (not schema-per-tenant) | Simpler migrations; works with connection pooling |
| Soft deletes (DocumentType) | `is_active = False` | Preserves referential integrity from SubDocument FKs |
| API key storage | SHA-256 hash only; prefix for display | Key never recoverable; user can still identify their keys |
| Storage proxy | 302 → presigned MinIO URL | MinIO credentials never reach the browser; no double-proxying |

## Database Schema Overview

13 tables across 3 logical groups:

**Identity & access**
- `tenants` — tenant registry with Stripe IDs
- `users` — tenant-scoped users (admin / reviewer / viewer roles)
- `api_keys` — hashed API keys with scopes and expiry

**Document processing**
- `documents` — uploaded PDFs with processing status
- `subdocuments` — page ranges detected by boundary detection (`INT4RANGE`)
- `extracted_fields` — per-field extraction results with bbox + confidence + LLM reasoning
- `pipeline_runs` — execution history with per-stage timing (used for P95 metrics)
- `usage_records` — metered usage events (pages processed, LLM tokens)

**Configuration**
- `document_types` — field schemas with classification hints
- `document_type_fields` — individual field definitions
- `validation_rules` — per-field and cross-field rules

**Integrations**
- `webhooks` — configured webhook endpoints (URL, events, HMAC secret)
- `webhook_deliveries` — delivery log with retry tracking
