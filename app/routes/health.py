"""
Health check endpoint
"""

from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "Blind Spot AI Thinking Companion",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Blind Spot AI Thinking Companion API",
        "docs": "/docs",
        "health": "/health"
    }