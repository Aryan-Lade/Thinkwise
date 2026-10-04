"""
Application configuration using pydantic-settings
Integrates Google Secret Manager for runtime secret injection with graceful fallback.
"""

import logging
import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def load_secret_from_secret_manager(
    secret_id: str, project_id: Optional[str] = None
) -> Optional[str]:
    """
    Load a secret from Google Secret Manager.

    Gracefully degrades to local environment variables if Secret Manager is
    unavailable, credentials are missing, or running outside Google Cloud.
    """
    try:
        from google.cloud import secretmanager

        project = (
            project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        )
        if not project:
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        secret_value = response.payload.data.decode("UTF-8").strip()
        if secret_value:
            logger.info("Successfully fetched %s from Google Secret Manager", secret_id)
            return secret_value
    except Exception as err:
        logger.debug("Google Secret Manager lookup bypassed or unavailable: %s", err)
    return None


class Settings(BaseSettings):
    """Application settings with Google Secret Manager support."""

    # API Configuration
    GEMINI_API_KEY: str = Field(
        default_factory=lambda: (
            load_secret_from_secret_manager("GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY", "")
        ),
        description="Google Gemini API key",
    )
    PORT: int = Field(default=8080, description="Port to run the application on")
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment (development/production/testing)",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(default=["*"], description="Allowed CORS origins")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Rate limit requests per window"
    )
    RATE_LIMIT_WINDOW: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Cache Configuration
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds (5 minutes)")
    CACHE_MAXSIZE: int = Field(
        default=100, description="Maximum number of entries in cache"
    )
    SESSION_TTL_HOURS: int = Field(default=24, description="Session TTL in hours")

    # Gemini Configuration
    GEMINI_MODEL: str = Field(
        default="gemini-flash-lite-latest", description="Gemini model to use"
    )
    GEMINI_TEMPERATURE: float = Field(default=0.7, description="Gemini temperature")
    GEMINI_MAX_RETRIES: int = Field(default=3, description="Max retries for Gemini API")

    # Security
    MAX_REQUEST_SIZE: int = Field(
        default=1024 * 1024, description="Max request size in bytes (1MB)"
    )
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        allowed_envs = ["development", "production", "testing"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v.lower()


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
