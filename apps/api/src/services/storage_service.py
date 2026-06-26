# SPDX-License-Identifier: AGPL-3.0-or-later
import io
from miniopy_async import Minio
from ..config import settings


class StorageService:
    def __init__(self) -> None:
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self._bucket = settings.minio_bucket

    async def ensure_bucket(self) -> None:
        found = await self._client.bucket_exists(self._bucket)
        if not found:
            await self._client.make_bucket(self._bucket)

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        await self.ensure_bucket()
        await self._client.put_object(
            self._bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return key

    async def download(self, key: str) -> bytes:
        response = await self._client.get_object(self._bucket, key)
        return await response.read()

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        from datetime import timedelta
        return await self._client.presigned_get_object(
            self._bucket, key, expires=timedelta(seconds=expires_seconds)
        )

    async def delete(self, key: str) -> None:
        await self._client.remove_object(self._bucket, key)

    @staticmethod
    def document_key(tenant_id: str, doc_id: str) -> str:
        from datetime import datetime, UTC
        now = datetime.now(UTC)
        return f"{tenant_id}/{now.year}/{now.month:02d}/{doc_id}/original.pdf"

    @staticmethod
    def thumbnail_key(tenant_id: str, doc_id: str, page: int) -> str:
        from datetime import datetime, UTC
        now = datetime.now(UTC)
        return f"{tenant_id}/{now.year}/{now.month:02d}/{doc_id}/thumbs/page_{page:04d}.webp"

    @staticmethod
    def subdocument_key(tenant_id: str, doc_id: str, subdoc_id: str) -> str:
        from datetime import datetime, UTC
        now = datetime.now(UTC)
        return f"{tenant_id}/{now.year}/{now.month:02d}/{doc_id}/subdocs/{subdoc_id}.pdf"
