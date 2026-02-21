"""
Celery task: 4-step document ingestion pipeline.
parsing → chunking → embedding → storing

Status is persisted to MySQL at each step (not just Celery state).
"""

import uuid

from qdrant_client.models import PointStruct, Distance, VectorParams

from core.celery_app import celery
from core.vector_db import get_qdrant_client
from services.doc_ingest.helpers.query_helpers import (
    update_document_status,
    save_chunks,
    get_existing_chunks,
)
from services.doc_ingest.helpers.utils import (
    base64_to_bytes,
    extract_text_from_pdf,
    chunk_text,
    embed_batch,
    text_to_base64,
    base64_to_text,
    VECTOR_DIM,
)


from config.settings import settings

@celery.task(bind=True, name="services.doc_ingest.tasks.process_document")
def process_document(self, user_id: str, doc_id: str, b64_data: str):
    """
    Background pipeline for a single PDF document.
    Deduplicates text chunking by checking MySQL for existing Base64 chunks by doc_id.
    """
    try:
        # ── Check for existing chunks (Deduplication) ────────────
        existing_db_chunks = get_existing_chunks(doc_id)
        
        chunks = []
        if existing_db_chunks:
            # We already processed this document! Skip extracting + chunking.
            self.update_state(state="PROGRESS", meta={"step": "skipping_parsing (deduplicated)"})
            total_chunks = len(existing_db_chunks)
            for db_chunk in existing_db_chunks:
                chunks.append({
                    "chunk_index": db_chunk.chunk_index,
                    "page_number": db_chunk.page_number,
                    "text": db_chunk.chunk_text,  # This is the Base64 string!
                })
        else:
            # ── Step 1: PARSING ──────────────────────────────────────
            update_document_status(doc_id, "parsing")
            pdf_bytes = base64_to_bytes(b64_data)
            pages = extract_text_from_pdf(pdf_bytes)

            if not pages:
                raise ValueError("Could not extract text from PDF")

            # ── Step 2: CHUNKING ─────────────────────────────────────
            from config.settings import settings
            update_document_status(doc_id, "chunking")
            raw_chunks = chunk_text(pages, max_tokens=settings.CHUNK_SIZE)
            
            # Convert text to Base64
            for c in raw_chunks:
                chunks.append({
                    "chunk_index": c["chunk_index"],
                    "page_number": c["page_number"],
                    "text": text_to_base64(c["text"]),  # Store Base64 instead of plain text
                })
            
            total_chunks = len(chunks)
            if total_chunks == 0:
                raise ValueError("No chunks generated from PDF")

            update_document_status(doc_id, "chunking", total_chunks=total_chunks)
            
            # Save Base64 chunks to MySQL
            save_chunks(doc_id, chunks)

        # ── Step 3: EMBEDDING ────────────────────────────────────
        update_document_status(doc_id, "embedding", total_chunks=total_chunks)

        # We must decode Base64 back to plain text for the embedding model to understand it
        plain_texts = [base64_to_text(c["text"]) for c in chunks]
        all_vectors: list[list[float]] = []

        for i in range(0, len(plain_texts), settings.EMBED_BATCH_SIZE):
            batch = plain_texts[i : i + settings.EMBED_BATCH_SIZE]
            vectors = embed_batch(batch)
            all_vectors.extend(vectors)

        # ── Step 4: STORING ──────────────────────────────────────
        update_document_status(doc_id, "storing", total_chunks=total_chunks)

        collection_name = f"doc_{user_id}"
        client = get_qdrant_client()

        # ensure collection exists
        existing = [col.name for col in client.get_collections().collections]
        if collection_name not in existing:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )

        # build points — using the Base64 chunks in the payload!
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "doc_id": doc_id,
                    "user_id": user_id,
                    "text": chunks[idx]["text"],  # Base64 string
                    "page_number": chunks[idx]["page_number"],
                    "chunk_index": chunks[idx]["chunk_index"],
                },
            )
            for idx, vec in enumerate(all_vectors)
        ]

        # upsert in batches of 100
        for i in range(0, len(points), 100):
            client.upsert(
                collection_name=collection_name,
                points=points[i : i + 100],
            )

        # ── DONE ─────────────────────────────────────────────────
        update_document_status(doc_id, "ready", total_chunks=total_chunks)

        return {"status": "ready", "chunks_stored": total_chunks}

    except Exception as exc:
        update_document_status(doc_id, "failed", error=str(exc))
        raise exc
