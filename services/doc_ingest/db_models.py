"""
SQLAlchemy ORM models for document ingestion.
"""

from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, BigInteger
from sqlalchemy.orm import relationship

from core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id          = Column(String(36), primary_key=True)               # UUID doc_id
    user_id     = Column(String(100), nullable=False, index=True)
    filename    = Column(String(255), nullable=False)
    file_size   = Column(BigInteger, nullable=True)
    status      = Column(
        Enum("queued", "parsing", "chunking", "embedding", "storing", "ready", "failed",
             name="doc_status"),
        default="queued",
        nullable=False,
        index=True,
    )
    error        = Column(Text, nullable=True)
    total_chunks = Column(Integer, default=0)
    job_id       = Column(String(255), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document {self.id} — {self.status}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id          = Column(String(36), primary_key=True)               # UUID
    doc_id      = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    chunk_text  = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk {self.id} chunk={self.chunk_index}>"
