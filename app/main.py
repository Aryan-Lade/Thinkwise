"""
Blind Spot AI Thinking Companion - Main Application Entry Point
"""

import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routes import health, analyze, refine, summary

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Static directory
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Create FastAPI app
app = FastAPI(
    title="Blind Spot AI Thinking Companion",
    description="AI-powered tool to help users identify blind spots in their reasoning",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(refine.router, prefix="/api/v1", tags=["refine"])
app.include_router(summary.router, prefix="/api/v1", tags=["summary"])

# Mount static assets (JS/CSS bundles from DealMind build)
if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

# Mount Thinkwise CSS and JS directories
if (STATIC_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")

if (STATIC_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")

# Serve specific static files directly
@app.get("/favicon.svg")
async def favicon():
    return FileResponse(str(STATIC_DIR / "favicon.svg"))

@app.get("/icons.svg")
async def icons():
    return FileResponse(str(STATIC_DIR / "icons.svg"))

# Catch-all: serve index.html for all non-API routes (React Router SPA)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """Serve the React SPA for all non-API, non-asset routes."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend not found"}

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Blind Spot AI Thinking Companion starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Port: {settings.PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Blind Spot AI Thinking Companion shutting down...")