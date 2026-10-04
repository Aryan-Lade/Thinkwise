import sys
from pathlib import Path
from urllib.parse import parse_qs

# Add project root directory to sys.path so "app" modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as fastapi_app

async def app(scope, receive, send):
    """ASGI entrypoint for Vercel Serverless Functions."""
    if scope.get("type") == "http":
        query_string = scope.get("query_string", b"").decode("utf-8")
        qs = parse_qs(query_string)
        if "__path" in qs and qs["__path"]:
            sub = qs["__path"][0].lstrip("/")
            scope["path"] = f"/api/{sub}"
        elif scope.get("path", "").startswith("/api/index.py"):
            scope["path"] = scope["path"][len("/api/index.py"):] or "/"



    await fastapi_app(scope, receive, send)

__all__ = ["app"]
