from fastapi import APIRouter
from core.settings import settings
from datetime import datetime

index_router = APIRouter(tags=["Index"])

@index_router.get("/")
async def index() -> dict[str, str]:
    return {"message": f"{settings.PROJECT.NAME}"}

@index_router.get("/health")
async def health() -> dict[str, str]:
    return {
        "message": "OK",
        "status": "healthy",
        "version": settings.PROJECT.VERSION,
        "timestamp": datetime.now().isoformat()
    }