import os
from fastapi import APIRouter
from config.settings import settings
from fastapi import HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


def home():
    print(settings.HOME_HTML_PATH)
    if not os.path.exists(settings.HOME_HTML_PATH):
        raise HTTPException(status_code=404, detail="home.html not found")
    return FileResponse(settings.HOME_HTML_PATH, media_type="text/html")


handlers = [
    {
        "path": "/",
        "endpoint": home,
        "methods": ["GET"]
    }
]

for route in handlers:
    router.add_api_route(
        path=route["path"],
        endpoint=route["endpoint"],
        methods=route["methods"]
    )
