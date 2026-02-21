from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base settings for the application."""

    # Qdrant settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    HOME_HTML_PATH: str = "/app/templates/home.html"

    class Config:
        env_file = ".env"
        validate_by_name = True
        extra = "ignore"

settings = Settings()