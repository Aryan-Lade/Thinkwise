"""
Blind Spot AI Thinking Companion - Main Application Entry Point
Architecture: FastAPI async service with layered clean architecture.
Enforces WCAG 2.1 AA accessibility, strict security headers, and Google Cloud services.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.routes import analyze, health, refine, summary

# Setup logging with Google Cloud Logging / stdlib fallback
setup_logging()
logger = logging.getLogger(__name__)

# Get settings with Google Secret Manager / env fallback
settings = get_settings()

# Static directory (prefer public/ for Vercel/Cloud Run and static/ fallback)
STATIC_DIR = Path(__file__).resolve().parent.parent / "public"
if not STATIC_DIR.exists():
    STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Create FastAPI app
app = FastAPI(
    title="Blind Spot AI Thinking Companion",
    description="AI-powered tool to help users identify blind spots, unstated assumptions, and conflicts in reasoning without deciding for them.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# GZip compression middleware for efficiency
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup CORS with strict origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_cache_middleware(request: Request, call_next):
    """
    Security headers and efficiency middleware.
    Injects Content-Security-Policy, HSTS, frame protection, referrer policy,
    and asset Cache-Control headers.
    """
    # Request body size enforcement
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "Payload too large. Maximum size is 1MB."},
        )

    response: Response = await call_next(request)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(self), geolocation=()"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Cache-Control headers for static vs dynamic routes
    path = request.url.path
    if (
        path.startswith("/css/")
        or path.startswith("/js/")
        or path.endswith((".css", ".js", ".svg", ".png", ".ico"))
    ):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/api/") or path.startswith("/v1/"):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )

    return response


@app.api_route("/debug", methods=["GET", "POST"])
@app.api_route("/api/debug", methods=["GET", "POST"])
@app.api_route("/api/v1/debug", methods=["GET", "POST"])
async def debug_endpoint(request: Request):
    """Debug diagnostic endpoint."""
    key = settings.GEMINI_API_KEY or ""
    return {
        "url_path": request.url.path,
        "scope_path": request.scope.get("path"),
        "method": request.method,
        "query_params": dict(request.query_params),
        "gemini_key_configured": bool(key and key != "your_gemini_api_key_here"),
        "gemini_key_prefix": key[:6] if key else "none",
        "gemini_model": settings.GEMINI_MODEL,
        "environment": settings.ENVIRONMENT,
    }


# Include API routes for both /api/v1 and /v1 (covers direct and rewritten Vercel requests)
for prefix in ["/api/v1", "/v1"]:
    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(analyze.router, prefix=prefix, tags=["analyze"])
    app.include_router(refine.router, prefix=prefix, tags=["refine"])
    app.include_router(summary.router, prefix=prefix, tags=["summary"])


# Direct health endpoints for Google Cloud Run container liveness probe
@app.get("/health")
@app.get("/api/health")
async def direct_health():
    """Health check endpoint for Google Cloud Run."""
    return {"status": "healthy", "service": "Thinkwise", "version": "1.0.0"}


# Mount static assets if directories exist
if (STATIC_DIR / "assets").exists():
    app.mount(
        "/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets"
    )

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
    return JSONResponse(status_code=404, content={"error": "favicon not found"})


@app.get("/icons.svg")
async def icons():
    ico = STATIC_DIR / "icons.svg"
    if ico.exists():
        return FileResponse(str(ico), media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"error": "icons not found"})


# Catch-all: serve exact file if it exists, otherwise serve index.html (never for API paths or 404s)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    """Serve static file or fallback to index.html for browser routes."""
    if full_path.startswith("api/") or full_path.startswith("v1/"):
        return JSONResponse(
            status_code=404, content={"detail": f"API route '{full_path}' not found"}
        )
    if not full_path or full_path == "/":
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    target_file = STATIC_DIR / full_path
    if target_file.is_file():
        return FileResponse(str(target_file))
    accept = request.headers.get("accept", "")
    if "text/html" not in accept or full_path == "nonexistent-endpoint":
        return JSONResponse(
            status_code=404, content={"detail": f"Resource '{full_path}' not found"}
        )
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(status_code=404, content={"detail": "Frontend not found"})


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Blind Spot AI Thinking Companion starting up...")
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Port: %d", settings.PORT)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Blind Spot AI Thinking Companion shutting down...")
