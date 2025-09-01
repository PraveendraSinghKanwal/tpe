from fastapi import APIRouter
from app.api.v1.routers import health, tpe_router

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(tpe_router.router, prefix="/tpe", tags=["tps"])
api_router.include_router(health.router, tags=["health"])
