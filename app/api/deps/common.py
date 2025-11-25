from fastapi import Depends, HTTPException
from datetime import datetime
from app.core.config import settings


def get_current_timestamp() -> datetime:
    """Get current timestamp for responses"""
    return datetime.utcnow()


def get_app_info() -> dict:
    """Get application information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }