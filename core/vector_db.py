from qdrant_client import QdrantClient
import os


def get_qdrant_client():
    client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333)),
)
    return client