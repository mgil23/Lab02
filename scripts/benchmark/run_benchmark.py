#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
P95 benchmark for OpenIDP pipeline.
Usage: python scripts/benchmark/run_benchmark.py --count 20 --api-url http://localhost:8000
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

STAGE_ORDER = ["ingest", "preprocess", "classify_split", "ocr", "extract", "persist"]
P95_BUDGETS_MS = {
    "ingest": 3_000,
    "preprocess": 8_000,
    "classify_split": 6_000,
    "ocr": 15_000,
    "extract": 18_000,
    "persist": 5_000,
    "total": 55_000,
}


async def upload_and_wait(
    client: httpx.AsyncClient,
    api_url: str,
    pdf_path: Path,
    tenant: str,
    token: str,
) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    with open(pdf_path, "rb") as f:
        resp = await client.post(
            f"{api_url}/api/v1/{tenant}/documents",
            files={"file": (pdf_path.name, f, "application/pdf")},
            headers=headers,
            timeout=30.0,
        )
    resp.raise_for_status()
    doc_id = resp.json()["id"]

    # Poll until completed or failed
    t0 = time.monotonic()
    while True:
        await asyncio.sleep(2)
        resp = await client.get(
            f"{api_url}/api/v1/{tenant}/documents/{doc_id}/pipeline-status",
            headers=headers,
            timeout=10.0,
        )
        status = resp.json()
        if status.get("status") in ("completed", "failed"):
            status["total_elapsed_ms"] = int((time.monotonic() - t0) * 1000)
            return status
        if time.monotonic() - t0 > 120:
            raise TimeoutError(f"Document {doc_id} timed out after 120s")


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = max(0, int(len(sorted_v) * 0.95) - 1)
    return sorted_v[idx]


async def run_benchmark(
    api_url: str,
    pdf_path: Path,
    count: int,
    tenant: str,
    token: str,
) -> None:
    async with httpx.AsyncClient() as client:
        stage_durations: dict[str, list[float]] = {s: [] for s in STAGE_ORDER}
        total_durations: list[float] = []
        failures = 0

        print(f"Running {count} iterations with {pdf_path.name}...")
        for i in range(count):
            try:
                result = await upload_and_wait(client, api_url, pdf_path, tenant, token)
                if result.get("status") == "failed":
                    failures += 1
                    print(f"  [{i+1}/{count}] FAILED: {result.get('error_message')}")
                    continue

                total_durations.append(result["total_elapsed_ms"])
                stages = result.get("stages", {})
                for stage in STAGE_ORDER:
                    if stage in stages and stages[stage].get("duration_ms"):
                        stage_durations[stage].append(stages[stage]["duration_ms"])

                print(f"  [{i+1}/{count}] OK — {result['total_elapsed_ms']}ms total")
            except Exception as e:
                failures += 1
                print(f"  [{i+1}/{count}] ERROR: {e}")

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Runs: {count} total, {failures} failed, {count - failures} succeeded")
    print()

    all_pass = True
    for stage in STAGE_ORDER:
        vals = stage_durations[stage]
        if not vals:
            print(f"  {stage:20s} — no data")
            continue
        p95_val = p95(vals)
        budget = P95_BUDGETS_MS[stage]
        status = "PASS" if p95_val <= budget else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(
            f"  {stage:20s}  P95={p95_val:6.0f}ms  budget={budget}ms  [{status}]"
            f"  (n={len(vals)}, avg={statistics.mean(vals):.0f}ms)"
        )

    total_p95 = p95(total_durations) if total_durations else 0
    total_budget = P95_BUDGETS_MS["total"]
    total_status = "PASS" if total_p95 <= total_budget else "FAIL"
    if total_status == "FAIL":
        all_pass = False

    print()
    print(
        f"  {'TOTAL':20s}  P95={total_p95:6.0f}ms  budget={total_budget}ms  [{total_status}]"
    )
    print("=" * 60)
    sys.exit(0 if all_pass else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenIDP P95 benchmark")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--pdf", default="scripts/benchmark/golden-datasets/sample-15page.pdf")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--tenant", default="benchmark-tenant")
    parser.add_argument("--token", required=True, help="Bearer token for authentication")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    asyncio.run(run_benchmark(args.api_url, pdf_path, args.count, args.tenant, args.token))


if __name__ == "__main__":
    main()
