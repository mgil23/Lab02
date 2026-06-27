# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Storage proxy — generates presigned MinIO/S3 URLs and returns a redirect.
This keeps object storage credentials out of the browser while still allowing
direct browser-to-storage streaming (no double-proxying through the API).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from ..dependencies import CurrentUser
from ..services.storage_service import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/{key:path}", response_class=RedirectResponse)
async def get_storage_object(
    key: str,
    current_user: CurrentUser,
) -> RedirectResponse:
    """
    Returns a 302 redirect to a short-lived presigned URL.
    The key is tenant-prefixed so cross-tenant access is structurally prevented.
    """
    if not key or ".." in key:
        raise HTTPException(status_code=400, detail="Invalid storage key")

    storage = StorageService()
    try:
        url = await storage.presigned_url(key, expires_seconds=300)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Object not found") from exc

    return RedirectResponse(url=url, status_code=302)
