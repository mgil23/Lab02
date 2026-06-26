# SPDX-License-Identifier: AGPL-3.0-or-later
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.document import Document, DocumentStatus
from ..services.storage_service import StorageService


class DocumentService:
    def __init__(self, db: AsyncSession, storage: StorageService) -> None:
        self._db = db
        self._storage = storage

    async def create_and_enqueue(
        self,
        tenant_id: uuid.UUID,
        filename: str,
        contents: bytes,
        created_by: uuid.UUID | None = None,
    ) -> Document:
        import fitz  # PyMuPDF
        from ..core.rls import tenant_context

        # Quick metadata extraction
        with fitz.open(stream=contents, filetype="pdf") as pdf:
            page_count = pdf.page_count

        doc_id = uuid.uuid4()
        storage_key = StorageService.document_key(str(tenant_id), str(doc_id))

        async with tenant_context(self._db, tenant_id):
            doc = Document(
                id=doc_id,
                tenant_id=tenant_id,
                filename=filename,
                storage_key=storage_key,
                file_size=len(contents),
                page_count=page_count,
                status=DocumentStatus.PENDING,
                created_by=created_by,
            )
            self._db.add(doc)
            await self._db.flush()

        # Upload to MinIO
        await self._storage.upload(storage_key, contents, "application/pdf")

        # Enqueue pipeline
        from arq import create_pool
        from arq.connections import RedisSettings
        from ..config import settings
        pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        await pool.enqueue_job(
            "run_pipeline",
            str(doc_id),
            str(tenant_id),
            _queue_name="pipeline",
        )
        await pool.aclose()

        return doc
