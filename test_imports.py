#!/usr/bin/env python3
"""
Test script to verify that all modules can be imported correctly.
"""

def test_imports():
    """Test importing all major components."""
    try:
        print("Testing config import...")
        from app.core.config import get_settings
        settings = get_settings()
        print(f"* Config loaded. Environment: {settings.ENVIRONMENT}")

        print("Testing constants import...")
        from app.core import constants
        print(f"* Constants loaded. Cache TTL: {constants.DEFAULT_CACHE_TTL}")

        print("Testing errors import...")
        from app.core.errors import BlindSpotException
        print("* Errors loaded")

        print("Testing logging import...")
        from app.core.logging import setup_logging
        print("* Logging loaded")

        print("Testing models import...")
        from app.models.schemas import AnalysisResponse
        print("* Models loaded")

        print("Testing services import...")
        from app.services.gemini_service import gemini_service
        from app.services.guard_service import guard_service
        from app.services.session_service import session_service
        from app.services.cache_service import cache_service
        from app.services.safety_service import safety_service
        print("* Services loaded")

        print("Testing routes import...")
        from app.routes.health import router as health_router
        from app.routes.analyze import router as analyze_router
        from app.routes.refine import router as refine_router
        from app.routes.summary import router as summary_router
        print("* Routes loaded")

        print("Testing main app import...")
        from app.main import app
        print("* Main app loaded")

        print("\nAll imports successful! *")
        return True

    except Exception as e:
        print(f"\n! Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)