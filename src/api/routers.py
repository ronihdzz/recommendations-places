from fastapi import APIRouter
from api.v1.places.endpoints import router as places_endpoints

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(places_endpoints)