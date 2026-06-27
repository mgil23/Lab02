# SPDX-License-Identifier: AGPL-3.0-or-later
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from .service import OcrService

app = FastAPI(title="OpenIDP OCR Engine", version="1.0.0")
_svc = OcrService()


class OcrRequest(BaseModel):
    images_b64: list[str]


class OcrPageResult(BaseModel):
    blocks: list[dict]


class OcrResponse(BaseModel):
    pages: list[OcrPageResult]


@app.post("/ocr/pages", response_model=OcrResponse)
async def ocr_pages(body: OcrRequest) -> OcrResponse:
    if not body.images_b64:
        raise HTTPException(status_code=400, detail="No images provided")
    if len(body.images_b64) > 50:
        raise HTTPException(status_code=400, detail="Max 50 pages per request")

    results = await _svc.ocr_pages(body.images_b64)
    return OcrResponse(pages=[OcrPageResult(**r) for r in results])


@app.post("/structure/layout")
async def layout_analysis(request: Request) -> dict:
    """Accepts raw image bytes in the request body, returns layout blocks."""
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No image data")
    return await _svc.layout_page(body)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ocr-engine"}
