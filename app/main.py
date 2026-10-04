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

# Static directory (prefer public/ for Vercel and static/ for local)
STATIC_DIR = Path(__file__).resolve().parent.parent / "public"
if not STATIC_DIR.exists():
    STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Create FastAPI app
app = FastAPI(
    title="Blind Spot AI Thinking Companion",
    description="AI-powered tool to help users identify blind spots in their reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/debug", methods=["GET", "POST"])
@app.api_route("/api/debug", methods=["GET", "POST"])
@app.api_route("/api/v1/debug", methods=["GET", "POST"])
async def debug_endpoint(request: Request):
    return {
        "url_path": request.url.path,
        "scope_path": request.scope.get("path"),
        "method": request.method,
        "query_params": dict(request.query_params),
        "headers": {k: v for k, v in request.headers.items() if "auth" not in k.lower() and "key" not in k.lower()}
    }



# Include API routes for both /api/v1 and /v1 (covers direct and rewritten Vercel requests)
for prefix in ["/api/v1", "/v1"]:
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(analyze.router, prefix=prefix, tags=["analyze"])
    app.include_router(refine.router, prefix=prefix, tags=["refine"])
    app.include_router(summary.router, prefix=prefix, tags=["summary"])

# Direct health endpoints
@app.get("/health")
@app.get("/api/health")
async def direct_health():
    return {"status": "healthy", "service": "Thinkwise", "version": "1.0.0"}

# Mount static assets if directories exist
if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

if (STATIC_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")

if (STATIC_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")

# Serve specific static files directly
@app.get("/favicon.svg")
async def favicon():
    fav = STATIC_DIR / "favicon.svg"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/svg+xml")
    return {"error": "favicon not found"}

@app.get("/icons.svg")
async def icons():
    ico = STATIC_DIR / "icons.svg"
    if ico.exists():
        return FileResponse(str(ico), media_type="image/svg+xml")
    return {"error": "icons not found"}

# Catch-all: serve exact file if it exists, otherwise serve index.html (never for API paths)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """Serve static file or fallback to index.html."""
    if full_path.startswith("api/") or full_path.startswith("v1/"):
        return {"error": "API route not found", "requested_path": full_path}
    target_file = STATIC_DIR / full_path
    if target_file.is_file():
        return FileResponse(str(target_file))
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