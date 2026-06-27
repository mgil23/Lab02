# SPDX-License-Identifier: AGPL-3.0-or-later
"""End-to-end pipeline tests — requires running services."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_and_pipeline(client: AsyncClient) -> None:
    """Register → upload PDF → check pipeline progress."""
    # Register tenant
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "tenant_name": "Test Tenant",
        "tenant_slug": "test-tenant",
    })
    assert resp.status_code == 201
    tokens = resp.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Upload a minimal PDF
    from io import BytesIO
    import fitz
    pdf_doc = fitz.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 50), "Invoice #12345\nAmount Due: $500.00\nDate: 2026-01-15")
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    resp = await client.post(
        "/api/v1/test-tenant/documents",
        files={"file": ("invoice.pdf", BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 202
    doc_id = resp.json()["id"]

    # Check document exists
    resp = await client.get(f"/api/v1/test-tenant/documents/{doc_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["filename"] == "invoice.pdf"


@pytest.mark.asyncio
async def test_classify_boundary_detection() -> None:
    """Unit test for multi-document boundary detection."""
    from src.pipeline.stages.classify import PageFeatures, detect_boundaries

    pages = [
        PageFeatures(1, "Invoice #1\nCompany A\nTotal: $100", "hash1", "Company A", False, False),
        PageFeatures(2, "Invoice #2\nPage 2 of 3\nLine items", "hash1", "Company A", False, False),
        PageFeatures(3, "Invoice #3\nPage 1 of 2\nCompany B", "hash2", "Company B", True, False),
        PageFeatures(4, "Invoice #4\nPage 2 of 2\nTotal: $200", "hash2", "Company B", False, False),
    ]
    boundaries = detect_boundaries(pages)
    assert 1 in boundaries  # Always starts at 1
    assert 3 in boundaries  # Boundary detected at page 3 (page restart + entity change)
