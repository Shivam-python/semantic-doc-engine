"""
Function helpers — orchestration layer for document ingestion.
Coordinates between utils, query_helpers, and the Celery task.
"""

import uuid

from services.doc_ingest.models import UploadResponse, StatusResponse
from services.doc_ingest.helpers.utils import pdf_to_base64
from services.doc_ingest.helpers.query_helpers import (
    create_document,
    get_document,
)


def handle_upload(file_bytes: bytes, filename: str, user_id: str) -> UploadResponse:
    """
    1. Generate doc_id
    2. Convert PDF bytes → base64 (for passing to Celery via Redis broker)
    3. Queue Celery background task
    4. Create document record in MySQL (status=queued)
    5. Return immediate response
    """
    doc_id = str(uuid.uuid4())
    b64_data = pdf_to_base64(file_bytes)

    # queue background processing (pass base64 data to worker via task args)
    from services.doc_ingest.tasks import process_document
    task = process_document.delay(user_id, doc_id, b64_data)
    job_id = task.id

    # persist document metadata in MySQL
    create_document(
        user_id=user_id,
        doc_id=doc_id,
        filename=filename,
        file_size=len(file_bytes),
        job_id=job_id,
    )

    return UploadResponse(
        doc_id=doc_id,
        job_id=job_id,
        status="processing",
        filename=filename,
    )


def get_document_status(user_id: str, doc_id: str) -> StatusResponse:
    """
    Read document status directly from MySQL.
    No Celery AsyncResult needed — the task updates MySQL at each step.
    """
    doc = get_document(user_id, doc_id)

    if doc is None:
        return StatusResponse(status="not_found", error="Document not found.")

    if doc.status == "ready":
        return StatusResponse(status="ready", chunks_stored=doc.total_chunks)

    elif doc.status == "failed":
        return StatusResponse(status="failed", error=doc.error)

    elif doc.status == "queued":
        return StatusResponse(status="queued")

    else:
        # parsing, chunking, embedding, storing
        return StatusResponse(
            status="processing",
            step=doc.status,
            total_chunks=doc.total_chunks,
        )
