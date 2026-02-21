from fastapi import APIRouter


router = APIRouter()

from routes.home import router as HomeRouter
from routes.health import router as HealthCheckRouter
from services.doc_ingest import router as DocIngestRouter

router.include_router(HomeRouter, prefix="", tags=["Home"])
router.include_router(HealthCheckRouter, prefix="/v1", tags=["Health-Check"])
router.include_router(DocIngestRouter, prefix="/api/v1/documents", tags=["Documents"])