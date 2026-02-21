"""
Document ingestion API endpoints (async).
- POST /upload  — accept PDF, return doc_id + job_id immediately
- GET  /{doc_id}/status — poll processing status
"""

from fastapi import APIRouter, UploadFile, File, Header, HTTPException

from services.doc_ingest.models import UploadResponse, StatusResponse
from services.doc_ingest.helpers.function_helpers import (
    handle_upload,
    get_document_status,
)
from config.settings import settings

router = APIRouter()

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    x_user_id: str = Header(...),
):
    """
    Accept a PDF upload, convert to base64, store in Redis,
    and queue background processing. Returns immediately.
    """
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB.",
        )

    response = handle_upload(file_bytes, file.filename, x_user_id)
    return response


@router.get("/{doc_id}/status", response_model=StatusResponse)
async def document_status(
    doc_id: str,
    x_user_id: str = Header(...),
):
    """
    Poll the current ingestion status for a given document.
    """
    response = get_document_status(x_user_id, doc_id)

    if response.status == "not_found":
        raise HTTPException(status_code=404, detail="Document not found.")

    return response
