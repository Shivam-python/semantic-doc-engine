"""
Pydantic models for the document ingestion service.
"""

from typing import Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    doc_id: str
    job_id: str
    status: str
    filename: str


class StatusResponse(BaseModel):
    status: str
    step: Optional[str] = None
    total_chunks: Optional[int] = None
    chunks_stored: Optional[int] = None
    error: Optional[str] = None
