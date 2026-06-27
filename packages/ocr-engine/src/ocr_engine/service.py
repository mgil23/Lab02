# SPDX-License-Identifier: AGPL-3.0-or-later
"""
PaddleOCR service with ONNX Runtime inference.
Uses ProcessPoolExecutor to bypass Python GIL for CPU-bound OCR.
"""
import asyncio
import base64
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Any

from .preprocessor import normalize_image, deskew, enhance_contrast

_ocr_instance: Any = None
_executor: ProcessPoolExecutor | None = None
_NUM_WORKERS = int(os.environ.get("OCR_WORKERS", "4"))


def _check_gpu() -> bool:
    try:
        import paddle
        return paddle.device.is_compiled_with_cuda()
    except Exception:
        return False


def _get_ocr() -> Any:
    """Process-local PaddleOCR singleton."""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        use_gpu = _check_gpu()
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            use_gpu=use_gpu,
            det_model_dir="/app/models/det",
            rec_model_dir="/app/models/rec",
            cls_model_dir="/app/models/cls",
            show_log=False,
            precision="fp16" if use_gpu else "fp32",
        )
    return _ocr_instance


def _ocr_page_sync(image_bytes: bytes) -> dict:
    """CPU-bound OCR for a single page image. Runs in subprocess."""
    import numpy as np
    ocr = _get_ocr()
    img = normalize_image(image_bytes)
    img = deskew(img)

    result = ocr.ocr(img, cls=True)
    blocks: list[dict] = []

    if result and result[0]:
        for line in result[0]:
            bbox, (text, confidence) = line
            xs = [p[0] for p in bbox]
            ys = [p[1] for p in bbox]
            blocks.append({
                "text": text,
                "confidence": round(float(confidence), 4),
                "bbox": {
                    "x": round(min(xs), 2),
                    "y": round(min(ys), 2),
                    "width": round(max(xs) - min(xs), 2),
                    "height": round(max(ys) - min(ys), 2),
                },
            })

    return {"blocks": blocks}


def _layout_page_sync(image_bytes: bytes) -> dict:
    """PP-Structure layout analysis for a single page."""
    from paddleocr import PPStructure

    img = normalize_image(image_bytes)
    engine = PPStructure(
        table=True,
        ocr=False,
        show_log=False,
        layout_model_dir="/app/models/layout",
        table_model_dir="/app/models/table",
    )
    result = engine(img)

    blocks: list[dict] = []
    tables: list[dict] = []

    for region in (result or []):
        region_type = region.get("type", "text").lower()
        bbox = region.get("bbox", [0, 0, 0, 0])

        block = {
            "type": region_type,
            "bbox": {
                "x": bbox[0], "y": bbox[1],
                "width": bbox[2] - bbox[0],
                "height": bbox[3] - bbox[1],
            },
        }

        if region_type == "table":
            table_html = region.get("res", {}).get("html", "")
            tables.append({**block, "html": table_html})
        else:
            text_lines = region.get("res", [])
            block["text"] = " ".join(
                line[1][0] for line in (text_lines or []) if line
            )
            blocks.append(block)

    return {"blocks": blocks, "tables": tables}


def _get_executor() -> ProcessPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=_NUM_WORKERS)
    return _executor


class OcrService:
    async def ocr_pages(self, page_images_b64: list[str]) -> list[dict]:
        """OCR multiple pages in parallel via subprocess pool."""
        loop = asyncio.get_event_loop()
        executor = _get_executor()

        tasks = [
            loop.run_in_executor(executor, _ocr_page_sync, base64.b64decode(img_b64))
            for img_b64 in page_images_b64
        ]
        return list(await asyncio.gather(*tasks))

    async def layout_page(self, image_bytes: bytes) -> dict:
        """Run PP-Structure layout analysis on a single page."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_get_executor(), _layout_page_sync, image_bytes)
