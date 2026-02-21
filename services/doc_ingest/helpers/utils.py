"""
Utility helpers for document ingestion.
- PDF ↔ base64 conversion
- Text extraction via PyMuPDF
- Text chunking (~400 tokens)
- Batch embedding via sentence-transformers
"""

import base64
import io

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer


from config.settings import settings

# ── Singleton embedding model ────────────────────────────────────────
_model: SentenceTransformer | None = None
EMBEDDING_MODEL_NAME = settings.EMBEDDING_MODEL_NAME
VECTOR_DIM = settings.VECTOR_DIM


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


# ── PDF ↔ Base64 ─────────────────────────────────────────────────────

def pdf_to_base64(file_bytes: bytes) -> str:
    """Encode raw PDF bytes into a base64 string."""
    return base64.b64encode(file_bytes).decode("utf-8")


def base64_to_bytes(b64_string: str) -> bytes:
    """Decode a base64 string back to raw PDF bytes."""
    return base64.b64decode(b64_string)


# ── Text ↔ Base64 ────────────────────────────────────────────────────

def text_to_base64(text: str) -> str:
    """Encode a plain text string to a Base64 string."""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def base64_to_text(b64_string: str) -> str:
    """Decode a Base64 string back to plain text."""
    return base64.b64decode(b64_string).decode("utf-8")


# ── Text Extraction ──────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Open PDF bytes with PyMuPDF, extract text page-by-page.
    Returns list of { page_number, text }.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").strip()
        if text:
            pages.append({"page_number": page_num + 1, "text": text})
    doc.close()
    return pages


import re

# ── Chunking ─────────────────────────────────────────────────────────

def chunk_text(pages: list[dict], max_tokens: int = 400) -> list[dict]:
    """
    Split page texts into chunks. Parses by sentences and tries to stop
    when the chunk length is closest to `max_tokens`.
    If adding a sentence crosses max_tokens, it compares the distance to max_tokens 
    with and without the sentence to decide whether to include it or start a new chunk.
    """
    chunks: list[dict] = []
    chunk_index = 0

    for page in pages:
        # Crude sentence splitting for English: look for . ! ? followed by space
        sentences = re.split(r'(?<=[.!?])\s+', page["text"])
        
        current: list[str] = []
        current_len = 0
        
        for sentence in sentences:
            sentence_len = len(sentence.split())
            if sentence_len == 0:
                continue
                
            if current_len + sentence_len > max_tokens:
                if current_len == 0:
                    # Single sentence larger than max_tokens, just take it
                    current.append(sentence)
                    chunks.append({
                        "page_number": page["page_number"],
                        "chunk_index": chunk_index,
                        "text": " ".join(current),
                    })
                    chunk_index += 1
                    current = []
                    current_len = 0
                else:
                    # Decide whether to stop BEFORE or AFTER this sentence
                    dist_before = max_tokens - current_len
                    dist_after = (current_len + sentence_len) - max_tokens
                    
                    if dist_before <= dist_after:
                        # Stopping before is closer (or equal). Finish current chunk.
                        chunks.append({
                            "page_number": page["page_number"],
                            "chunk_index": chunk_index,
                            "text": " ".join(current),
                        })
                        chunk_index += 1
                        current = [sentence]
                        current_len = sentence_len
                    else:
                        # Stopping after is closer. Include this sentence, then finish chunk.
                        current.append(sentence)
                        chunks.append({
                            "page_number": page["page_number"],
                            "chunk_index": chunk_index,
                            "text": " ".join(current),
                        })
                        chunk_index += 1
                        current = []
                        current_len = 0
            else:
                current.append(sentence)
                current_len += sentence_len
                
        if current:
            chunks.append({
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": " ".join(current),
            })
            chunk_index += 1

    return chunks


# ── Embedding ────────────────────────────────────────────────────────

def embed_batch(texts: list[str]) -> list[list[float]]:
    """Encode a list of text strings into dense vectors."""
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()
