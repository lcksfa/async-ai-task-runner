from fastapi import APIRouter
from app.api.v1.endpoints import health, tasks

api_router = APIRouter()

# Include health check endpoints
api_router.include_router(
    health.router,
    tags=["Health"]
)

# Include task endpoints
api_router.include_router(
    tasks.router,
    tags=["Tasks"]
)