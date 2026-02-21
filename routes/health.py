from fastapi import APIRouter


router = APIRouter()
def health_check():
    return {"status": "ok"}

handlers = [
    {
        "path": "/health-check",
        "endpoint": health_check,
        "methods": ["GET"]
    }
]

for route in handlers:
    router.add_api_route(
        path=route["path"],
        endpoint=route["endpoint"],
        methods=route["methods"]
    )
