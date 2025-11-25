from fastapi import APIRouter, Depends
from datetime import datetime
from app.schemas import HealthResponse
from app.core.config import settings
from app.api.deps.common import get_current_timestamp, get_app_info

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check(
    timestamp: datetime = Depends(get_current_timestamp),
    app_info: dict = Depends(get_app_info)
):
    """
    Health check endpoint to verify API is running.

    Returns:
        HealthResponse: API health status and metadata
    """
    return HealthResponse(
        status="healthy",
        app_name=app_info["name"],
        version=app_info["version"],
        timestamp=timestamp
    )