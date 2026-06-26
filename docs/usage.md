# Usage Guide

This guide walks through every feature of OpenIDP SaaS from first login to
production use.

---

## 1. Register your first tenant

Navigate to `http://localhost:3000/register` (or your deployment URL).

Fill in:
- **Company name** — becomes the tenant display name
- **Tenant slug** — URL-safe identifier, e.g. `acme-corp`. All your documents
  live under `/{slug}/...`.  Cannot be changed after creation.
- **Email + password** — creates the first admin user for this tenant

After registration you're redirected to `/{slug}/dashboard`.

---

## 2. Dashboard

The dashboard shows real-time KPIs for your tenant:

| Card | What it shows |
|------|--------------|
| Total Documents | All documents ever uploaded |
| Processing | Documents currently in the pipeline |
| Completed | Successfully extracted documents |
| Needs Review | Documents where LLM confidence was below threshold |
| Failed | Documents that errored during processing |
| Pages Processed Today | Metered usage for the current calendar day |
| Avg Processing Time | P50 pipeline duration across completed runs |

The chart below the cards shows completed vs. failed documents per day for
the last 7 days (adjustable to 30 or 90 days).

---

## 3. Upload a document

### Via the UI

1. Go to `/{slug}/documents/upload`
2. Drag-and-drop a PDF onto the drop zone, or click to browse
3. Only **PDF** files are accepted; maximum **100 MB** per file
4. A progress bar shows upload completion
5. On success you're redirected to the document's review workspace

### Via the API

```bash
curl -X POST http://localhost:8000/api/v1/{slug}/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf"
```

Response (HTTP 202 Accepted):
```json
{
  "id": "550e8400-...",
  "filename": "invoice.pdf",
  "status": "pending",
  "page_count": null,
  "created_at": "2025-01-01T12:00:00Z"
}
```

The document is immediately queued for processing. `page_count` is populated
once the ingest stage completes.

---

## 4. Processing pipeline

Processing runs automatically after upload. The pipeline has 6 stages:

```
pending → processing → (stages below) → completed | needs_review | failed
```

| Stage | What happens | Typical duration |
|-------|-------------|-----------------|
| **Ingest** | PyMuPDF reads page count + raw text; generates WebP thumbnails; uploads to MinIO | ≤ 3 s |
| **Preprocess** | PP-Structure detects layout blocks (text, tables, figures, headers) per page | ≤ 8 s |
| **Classify + Split** | Multi-signal boundary detector groups pages into sub-documents | ≤ 6 s |
| **OCR** | PaddleOCR ONNX runs on each sub-document in parallel (only needed for scanned pages) | ≤ 15 s |
| **Extract** | Strands Agent extracts and validates all fields per document type | ≤ 18 s |
| **Persist** | Results saved to DB; webhooks fired; WebSocket event sent | ≤ 5 s |

You can watch stage progress in real time in the review workspace — the status
banner at the top updates via WebSocket.

---

## 5. Review workspace

The review workspace is the core UI. It opens automatically after upload or from
the document list (`/{slug}/documents → click any row`).

### Layout

```
┌─ Status Banner ────────────────────────────────────────────────────┐
│ ● Completed in 42 s  ·  3 sub-documents                            │
├─ Sub-document Tabs ────────────────────────────────────────────────┤
│  [Doc 1 · invoice  pp. 1–3]  [Doc 2 · po  pp. 4–5]  [Doc 3 · ...]│
├─ PDF Viewer (55%) ──────────┬─ Extraction Panel (45%) ─────────────┤
│                              │  [Fields]  [Chat]                    │
│  PDF canvas with             │                                      │
│  bounding box                │  Field table with inline editing:    │
│  overlays (Konva)            │  field_name  │ value  │ confidence  │
│                              │  invoice_no  │ INV-42 │ 0.97 ✓      │
│  Click bbox → highlights     │  amount      │ $1,200 │ 0.91 ✓      │
│  corresponding field         │  vendor_name │ ACME   │ 0.65 ⚠ flag │
│                              │                                      │
│                              │  ── Evidence ──                     │
│                              │  Source: "Invoice #INV-42 dated..."  │
│                              │  Reasoning: "Found in header block..." │
└──────────────────────────────┴──────────────────────────────────────┘
```

### Bounding box sync

- **Click a field row** → PDF scrolls to the page containing that field and
  highlights its bounding box in yellow
- **Click a bounding box overlay** → the corresponding field row is highlighted
  in the table

### Editing extracted values

1. Click any cell in the **value** column to enter edit mode
2. Type the corrected value
3. Press **Enter** to save, **Escape** to cancel
4. Saved values are marked as `human_reviewed` (green checkmark)

### Evidence panel

Select any field to see:
- **Source text** — the exact text from the document that was used
- **LLM reasoning** — the chain-of-thought explanation from the Strands Agent

### Confidence indicators

| Icon | Meaning |
|------|---------|
| ✓ green | Confidence ≥ 0.85, validation passed |
| ⚠ yellow | Confidence 0.65–0.84 or soft validation warning |
| ✗ red | Confidence < 0.65, flagged for review, or validation error |

### Chat with document

Switch to the **Chat** tab in the extraction panel to ask questions about the
document in natural language:

```
You: What is the total amount due?
AI:  The total amount due is $1,200.00 as stated on page 2.
    The line items are: Widget A ($800), Widget B ($400).
```

Chat uses the extracted field values as context and calls the same Strands
Agent model.

---

## 6. Document types (low-code schema builder)

Document types define the fields the AI should extract from a class of document
(e.g. "Invoice", "Purchase Order", "Medical Record").

### Create a document type

1. Go to `/{slug}/config/document-types`
2. Click **New document type**
3. Fill in:
   - **Name** — display name (e.g. `Invoice`)
   - **Slug** — URL-safe identifier (e.g. `invoice`)
   - **Description** — helps the AI understand what this document type is
   - **Classification hints** — JSON hints for the classifier (e.g. `{"keywords": ["invoice", "bill to"]}`)

### Add fields

Each field has:

| Setting | Description |
|---------|-------------|
| Name | Machine-readable identifier, snake_case (e.g. `invoice_number`) |
| Label | Human-readable label (e.g. `Invoice Number`) |
| Type | `text`, `number`, `date`, `currency`, `boolean`, `table`, `address`, `email`, `phone` |
| Required | Whether missing value triggers a review flag |
| Config | Type-specific options (date format, currency symbol, etc.) |

### Add validation rules

Validation rules run after extraction:

| Rule type | Example |
|-----------|---------|
| `regex` | Invoice number matches `^INV-\d+$` |
| `range` | Amount is between 0 and 1,000,000 |
| `required` | Field must be non-empty |
| `cross_field` | `due_date` must be after `invoice_date` |
| `llm_semantic` | "Verify vendor name is a real company name" |

---

## 7. Playground (schema testing)

The playground lets you test a document type schema against raw text without
uploading a real file. Useful during schema development.

1. Go to `/{slug}/playground`
2. Select a document type
3. Paste document text
4. Click **Extract** — the Strands Agent runs and returns extracted fields

The playground calls `POST /{slug}/playground/extract` and does **not** create
any Document records.

---

## 8. API keys

For programmatic access (webhooks, integrations, CI pipelines):

1. Go to `/{slug}/settings/api-keys`
2. Click **Create API key**
3. Give it a name and optionally restrict scopes
4. **Copy the key now** — it is only shown once at creation

Use the key in requests:
```bash
curl http://localhost:8000/api/v1/{slug}/documents \
  -H "Authorization: Bearer oidp_xxxxxxxxxxxx"
```

API keys start with `oidp_`. The display in settings shows only the first 12
characters as an identifier; the full key is never retrievable.

---

## 9. Webhooks

Configure webhooks to receive HTTP POST notifications when pipeline events occur:

1. Go to `/{slug}/settings/webhooks`
2. Click **Add webhook**
3. Enter your endpoint URL
4. Select events:
   - `document.completed` — processing finished successfully
   - `document.failed` — pipeline failed
   - `document.needs_review` — flagged fields require human review
   - `extraction.field_updated` — a human reviewer saved a correction

Webhook payloads are signed with HMAC-SHA256. Verify the `X-OpenIDP-Signature`
header using your webhook's secret to reject spoofed requests.

---

## 10. Billing

The billing page (`/{slug}/billing`) shows:
- Current plan (Free / Starter / Professional / Enterprise)
- Pages processed this month vs. limit
- Subscription status

### Upgrade

Click **Upgrade** to open Stripe Checkout and select a plan:

| Plan | Monthly | Pages included | Users |
|------|---------|---------------|-------|
| Starter | $49 | 500 | 1 |
| Professional | $199 | 3,000 | 10 |
| Enterprise | Custom | Unlimited | Unlimited |

### Billing portal

Click **Manage billing** to open the Stripe customer portal where you can
update payment method, download invoices, and cancel.

---

## 11. Observability

| URL | Service | Default credentials |
|-----|---------|-------------------|
| `http://localhost:9090` | Prometheus | — |
| `http://localhost:3001` | Grafana | admin / admin |
| `http://localhost:9001` | MinIO Console | minioadmin / minioadmin123 |

Grafana comes pre-configured with the Prometheus data source. Import the
OpenIDP dashboard from `infra/grafana/openidp-dashboard.json` (if available)
or build your own queries against the `openidp_*` metric families.

---

## 12. Common operations

### Re-process a document

```bash
# Delete the document (cascades to subdocuments + extracted fields)
curl -X DELETE http://localhost:8000/api/v1/{slug}/documents/{id} \
  -H "Authorization: Bearer $TOKEN"

# Re-upload
curl -X POST http://localhost:8000/api/v1/{slug}/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"
```

### Check pipeline logs

```bash
docker compose -f infra/docker/docker-compose.dev.yml logs worker --follow
```

### Reset the database (development only)

```bash
docker compose -f infra/docker/docker-compose.dev.yml exec api \
  uv run alembic downgrade base
docker compose -f infra/docker/docker-compose.dev.yml exec api \
  uv run alembic upgrade head
```
