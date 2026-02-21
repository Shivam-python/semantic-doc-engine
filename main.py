
from redis import Redis
from fastapi import FastAPI
from qdrant_client.http.exceptions import UnexpectedResponse
from config.settings import settings
from core.vector_db import get_qdrant_client
from routes import router as v1_router
# -----------------------------
# App Initialization
# -----------------------------

app = FastAPI(
    title="Semantic Doc Engine : RAG",
    description="RAG-based technical document Q&A system",
    version="1.0.0",
)



# -----------------------------
# Startup Event
# -----------------------------

@app.on_event("startup")
def startup_event():
    print("Starting RAG service...")
    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed: {e}")

    # Check Qdrant connectivity
    try:
        client = get_qdrant_client()
        client.get_collections()
        print("Qdrant connected")
    except UnexpectedResponse as e:
        print(f"Qdrant error: {e}")
    except Exception as e:
        print(f"Qdrant connection failed: {e}")

    # Initialize MySQL tables
    try:
        from core.database import init_db
        init_db()
        print("MySQL tables initialized")
    except Exception as e:
        print(f"MySQL init failed: {e}")


# -----------------------------
# Health Check
# -----------------------------



app.include_router(v1_router)

