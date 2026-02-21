"""
Database engine, session factory, and declarative Base.
Uses SQLAlchemy with PyMySQL driver.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.settings import settings

engine = create_engine(
    settings.MYSQL_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on app startup."""
    from services.doc_ingest.db_models import Document, DocumentChunk  # noqa: F401
    Base.metadata.create_all(bind=engine)
