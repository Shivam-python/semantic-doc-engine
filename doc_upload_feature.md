# Document Ingestion API

This document provides a comprehensive overview of the Document Upload and Status feature added to the Semantic Document Engine.

## Overview

The feature provides an asynchronous pipeline to ingest PDF documents, extract text, split it into chunks, embed into vectors, and store them for Retrieval-Augmented Generation (RAG). It uses a microservices architecture to ensure the main API remains fast and responsive while heavy ML tasks run in the background.

## Architecture & Components

*   **FastAPI**: Provides the REST API endpoints (`/upload` and `/status`).
*   **Celery**: A distributed task queue that processes the PDF ingestion pipeline in the background.
*   **Redis**: Serves as the message broker for Celery, passing background tasks from FastAPI to the Celery worker.
*   **MySQL**: A relational database storing immediate document metadata (filename, ID, job status) and the extracted text chunks (encoded as `Base64`).
*   **Qdrant**: A high-performance vector database that stores the geometric embeddings and associated payload (the `Base64` chunks) for fast semantic similarity search.
*   **PyMuPDF (`fitz`)**: Used to extract text from the raw PDF files.
*   **sentence-transformers**: Machine learning model (`all-MiniLM-L6-v2`) used to encode text blocks into 384-dimensional dense vectors.

---

## 1. Document Upload API
**Endpoint:** `POST /api/v1/documents/upload`

### What It Does
When a user uploads a PDF, the API does **not** process the entire file immediately. Instead:
1. It validates the file size and type.
2. It generates a unique `doc_id` (UUID).
3. It creates a database record in the MySQL `documents` table with status `queued`.
4. It converts the raw PDF bytes into a Base64 string.
5. It fires off a background Celery task `process_document`, passing the Base64 data and `doc_id` to the worker.
6. It immediately returns the `doc_id`, the Celery `job_id`, and `status="processing"`.

### How to use via cURL
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "x-user-id: user_123" \
  -F "file=@/path/to/your/document.pdf"
```

*Response:*
```json
{
    "doc_id": "782f310d-7071-4d51-aa06-3396e1f2d7ab",
    "job_id": "891a23c7-c0a4-423b-81b0-d073a2af796c",
    "status": "processing",
    "filename": "document.pdf"
}
```

---

## 2. Background Processing Pipeline (Celery Worker)
Once the task is queued, the Celery worker picks it up and runs the `process_document` pipeline. The worker updates the MySQL database status at every step so the user can track progress.

**Step 1. Parsing**
*   **Status Update:** `parsing`
*   The worker decodes the Base64 PDF back to bytes.
*   It uses `PyMuPDF` to read the PDF and extract raw text page-by-page.

**Step 2. Chunking (Nearest-Boundary Strategy)**
*   **Status Update:** `chunking`
*   The raw text is split into chunks of approximately `CHUNK_SIZE` words (configurable in `config/settings.py` or `docker-compose.yml`, default `400`).
*   **Nearest-Boundary Logic:** The text is first split into individual sentences. When adding a sentence to a chunk pushes the word count over the limit, a mathematical distance algorithm checks if it is closer to the target limit *with* or *without* the final sentence. This ensures sentences are **never broken in half**, maintaining high semantic quality for embeddings.

**Step 3. Base64 Persistence & Deduplication**
*   Before embedding, the pipeline checks the MySQL `document_chunks` table for the specific `doc_id`. 
*   If chunks already exist for this ID, **it skips PDF parsing and chunking entirely**, pulls the database records, and jumps to Step 4 (Deduplication).
*   If chunks don't exist, it encodes each text chunk to `Base64` and saves them in the MySQL database. This ensures raw text is safely stored, deduplicated, and retrievable.

**Step 4. Embedding**
*   **Status Update:** `embedding`
*   The worker retrieves the Base64 text chunks, decodes them back to plain English, and batches them.
*   It uses `sentence-transformers` to generate dense vector representations (arrays of floats) for each chunk.

**Step 5. Storing in Qdrant**
*   **Status Update:** `storing`
*   The worker accesses the Qdrant database and ensures a collection exists for the specific user (`doc_{user_id}`).
*   It creates a "payload" for each embedding vector. The payload explicitly includes the `doc_id`, the `page_number`, and the **Base64 string of the text chunk**.
*   It upserts the vectors and payloads into Qdrant.

**Step 6. Completion**
*   **Status Update:** `ready`
*   The task concludes successfully, updating the MySQL database with `status="ready"` and recording the total number of chunks stored.

---

## 3. Document Status API
**Endpoint:** `GET /api/v1/documents/{doc_id}/status`

### What It Does
This endpoint allows the frontend/user to poll the progress of their upload. Instead of talking to the Celery broker (Redis) directly, this endpoint does a quick, lightweight `SELECT` query against the MySQL `documents` table.

It retrieves exactly which phase the Celery worker is currently processing (`parsing`, `chunking`, `embedding`, `storing`, `ready`, or `failed`).

### How to use via cURL
```bash
curl -X GET http://localhost:8000/api/v1/documents/782f310d-7071-4d51-aa06-3396e1f2d7ab/status \
  -H "x-user-id: user_123"
```

*Response while processing:*
```json
{
    "status": "processing",
    "step": "embedding",
    "total_chunks": 42,
    "chunks_stored": null,
    "error": null
}
```

*Response when finished:*
```json
{
    "status": "ready",
    "step": null,
    "total_chunks": null,
    "chunks_stored": 42,
    "error": null
}
```
