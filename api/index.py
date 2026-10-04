import sys
from pathlib import Path

# Add project root directory to sys.path so "app" modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app

# Vercel looks for the ASGI/WSGI callable named `app`
__all__ = ["app"]
