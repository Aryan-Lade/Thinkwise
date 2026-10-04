"""
Application configuration using pydantic-settings
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    PORT: int = Field(default=8080, description="Port to run the application on")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Rate limit requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # Cache Configuration
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds (5 minutes)")
    CACHE_MAXSIZE: int = Field(default=100, description="Maximum number of entries in cache")
    SESSION_TTL_HOURS: int = Field(default=24, description="Session TTL in hours")

    # Gemini Configuration
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model to use")
    GEMINI_TEMPERATURE: float = Field(default=0.7, description="Gemini temperature")
    GEMINI_MAX_RETRIES: int = Field(default=3, description="Max retries for Gemini API")

    # Security
    MAX_REQUEST_SIZE: int = Field(default=1024 * 1024, description="Max request size in bytes (1MB)")
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        allowed_envs = ["development", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()