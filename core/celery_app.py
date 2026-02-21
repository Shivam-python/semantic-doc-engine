from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "rag_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.doc_ingest.tasks"],
)

celery.conf.task_routes = {
    "app.tasks.*": {"queue": "default"},
}