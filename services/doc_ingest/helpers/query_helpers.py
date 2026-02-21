"""
Query helpers for document ingestion — MySQL operations.
CRUD operations on the documents and document_chunks tables.
"""

import uuid

from sqlalchemy.orm import Session

from core.database import SessionLocal
from services.doc_ingest.db_models import Document, DocumentChunk


# ── Document CRUD ────────────────────────────────────────────────────

def create_document(user_id: str, doc_id: str, filename: str, file_size: int, job_id: str) -> Document:
    """Insert a new document record with status='queued'."""
    db: Session = SessionLocal()
    try:
        doc = Document(
            id=doc_id,
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            job_id=job_id,
            status="queued",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    finally:
        db.close()


def get_document(user_id: str, doc_id: str) -> Document | None:
    """Fetch a document by user_id and doc_id."""
    db: Session = SessionLocal()
    try:
        return db.query(Document).filter(
            Document.id == doc_id,
            Document.user_id == user_id,
        ).first()
    finally:
        db.close()


def update_document_status(doc_id: str, status: str, error: str | None = None, total_chunks: int | None = None) -> None:
    """Update the status (and optionally error/total_chunks) of a document."""
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = status
            if error is not None:
                doc.error = error
            if total_chunks is not None:
                doc.total_chunks = total_chunks
            db.commit()
    finally:
        db.close()


# ── Chunk CRUD ───────────────────────────────────────────────────────

def get_existing_chunks(doc_id: str) -> list[DocumentChunk]:
    """Fetch all existing chunks for a document, ordered by chunk_index."""
    db: Session = SessionLocal()
    try:
        return db.query(DocumentChunk).filter(
            DocumentChunk.doc_id == doc_id
        ).order_by(DocumentChunk.chunk_index).all()
    finally:
        db.close()


def save_chunks(doc_id: str, chunks: list[dict]) -> None:
    """Bulk-insert chunk records for a document. Expects chunk_text to be Base64 if so configured."""
    db: Session = SessionLocal()
    try:
        chunk_records = [
            DocumentChunk(
                id=str(uuid.uuid4()),
                doc_id=doc_id,
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                chunk_text=c["text"],  # Could be plain text or Base64
            )
            for c in chunks
        ]
        db.bulk_save_objects(chunk_records)
        db.commit()
    finally:
        db.close()
