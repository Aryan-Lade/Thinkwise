"""
Application logging configuration
"""

import logging
import sys
from typing import Any, Dict

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
from google.oauth2 import service_account

from app.core.config import get_settings


def setup_logging() -> None:
    """Setup application logging."""
    settings = get_settings()

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Try to setup Google Cloud Logging if credentials are available
    try:
        # Check if we're running in Google Cloud environment
        # This will work if running on Cloud Run or if GOOGLE_APPLICATION_CREDENTIALS is set
        client = google.cloud.logging.Client()
        handler = CloudLoggingHandler(client)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logging.info("Google Cloud Logging enabled")
    except Exception as e:
        # Fallback to console logging only
        logging.warning(f"Google Cloud Logging not available: {e}. Using console logging only.")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)