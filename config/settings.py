from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base settings for the application."""

    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # MySQL settings
    MYSQL_URL: str = "mysql+pymysql://rag_user:rag_pass@localhost:3306/rag_db"

    # Chunking settings
    CHUNK_SIZE: int = 400
    
    # Upload settings
    MAX_FILE_SIZE_MB: int = 50
    
    # ML Model / Embedding settings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    VECTOR_DIM: int = 384
    EMBED_BATCH_SIZE: int = 64

    HOME_HTML_PATH: str = "/app/templates/home.html"

    class Config:
        env_file = ".env"
        validate_by_name = True
        extra = "ignore"

settings = Settings()