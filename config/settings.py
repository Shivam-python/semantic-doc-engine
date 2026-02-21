from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base settings for the application."""

    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    GEMINI_API_KEY: str = "sample_api_key"  # Replace with your actual API key or use environment variables

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    HOME_HTML_PATH: str = "/app/templates/home.html"
    
    COLLECTION_NAME: str = "gemini_embeddings"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    class Config:
        env_file = ".env"
        validate_by_name = True
        extra = "ignore"

settings = Settings()