from fastapi import APIRouter


router = APIRouter()

from routes.home import router as HomeRouter
from routes.health import router as HealthCheckRouter
from routes.query import router as QueryRouter

router.include_router(HomeRouter, prefix="", tags=["Home"])
router.include_router(HealthCheckRouter, prefix="/v1", tags=["Health-Check"])
router.include_router(QueryRouter, prefix="/v1", tags=["Query"])