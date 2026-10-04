"""
Cache service for optimizing repeated requests
"""

import hashlib
import json
import logging
from typing import Any, Optional, Tuple

from cachetools import TTLCache
from app.core.config import get_settings
from app.core.errors import BlindSpotException

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching AI responses and other expensive operations."""

    def __init__(self):
        """Initialize cache service."""
        settings = get_settings()

        # Cache for analysis responses
        self.analysis_cache = TTLCache(
            maxsize=settings.CACHE_MAXSIZE or 100,
            ttl=settings.CACHE_TTL
        )

        # Cache for refine responses
        self.refine_cache = TTLCache(
            maxsize=settings.CACHE_MAXSIZE or 100,
            ttl=settings.CACHE_TTL
        )

        # General purpose cache
        self.general_cache = TTLCache(
            maxsize=settings.CACHE_MAXSIZE or 200,
            ttl=settings.CACHE_TTL
        )

        self.settings = settings

    def _generate_cache_key(self, prefix: str, *args) -> str:
        """
        Generate a cache key from prefix and arguments.

        Args:
            prefix: Cache key prefix
            *args: Arguments to include in key

        Returns:
            MD5 hash of the combined arguments
        """
        # Create a string representation of all arguments
        key_data = {
            "prefix": prefix,
            "args": args
        }

        # Convert to JSON string for consistent hashing
        key_string = json.dumps(key_data, sort_keys=True)

        # Generate MD5 hash
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_analysis(
        self,
        decision: str,
        details: Optional[str],
        reasons: str,
        decision_type: Optional[str]
    ) -> Optional[Any]:
        """
        Get cached analysis response.

        Args:
            decision: The decision being considered
            details: Additional details
            reasons: Main reasons
            decision_type: Type of decision

        Returns:
            Cached analysis response if found, None otherwise
        """
        cache_key = self._generate_cache_key(
            "analysis",
            decision,
            details or "",
            reasons,
            decision_type or ""
        )

        cached_value = self.analysis_cache.get(cache_key)
        if cached_value is not None:
            logger.debug(f"Cache hit for analysis: {cache_key[:8]}...")
            return cached_value

        logger.debug(f"Cache miss for analysis: {cache_key[:8]}...")
        return None

    def set_analysis(
        self,
        decision: str,
        details: Optional[str],
        reasons: str,
        decision_type: Optional[str],
        value: Any
    ) -> None:
        """
        Cache an analysis response.

        Args:
            decision: The decision being considered
            details: Additional details
            reasons: Main reasons
            decision_type: Type of decision
            value: Analysis response to cache
        """
        cache_key = self._generate_cache_key(
            "analysis",
            decision,
            details or "",
            reasons,
            decision_type or ""
        )

        self.analysis_cache[cache_key] = value
        logger.debug(f"Cached analysis: {cache_key[:8]}...")

    def get_refine(
        self,
        session_id: str,
        answers_tuple: Tuple[Tuple[str, str], ...]
    ) -> Optional[Any]:
        """
        Get cached refine response.

        Args:
            session_id: Session identifier
            answers_tuple: Tuple of (question_id, answer) pairs

        Returns:
            Cached refine response if found, None otherwise
        """
        cache_key = self._generate_cache_key(
            "refine",
            session_id,
            answers_tuple
        )

        cached_value = self.refine_cache.get(cache_key)
        if cached_value is not None:
            logger.debug(f"Cache hit for refine: {cache_key[:8]}...")
            return cached_value

        logger.debug(f"Cache miss for refine: {cache_key[:8]}...")
        return None

    def set_refine(
        self,
        session_id: str,
        answers_tuple: Tuple[Tuple[str, str], ...],
        value: Any
    ) -> None:
        """
        Cache a refine response.

        Args:
            session_id: Session identifier
            answers_tuple: Tuple of (question_id, answer) pairs
            value: Refine response to cache
        """
        cache_key = self._generate_cache_key(
            "refine",
            session_id,
            answers_tuple
        )

        self.refine_cache[cache_key] = value
        logger.debug(f"Cached refine: {cache_key[:8]}...")

    def get_general(self, key: str) -> Optional[Any]:
        """
        Get value from general cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        return self.general_cache.get(key)

    def set_general(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in general cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        # For custom TTL, we would need a separate cache instance
        # For now, use the default TTL
        self.general_cache[key] = value
        logger.debug(f"Cached general item: {key[:8]}...")

    def clear_analysis_cache(self) -> None:
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        logger.info("Analysis cache cleared")

    def clear_refine_cache(self) -> None:
        """Clear the refine cache."""
        self.refine_cache.clear()
        logger.info("Refine cache cleared")

    def clear_all_caches(self) -> None:
        """Clear all caches."""
        self.analysis_cache.clear()
        self.refine_cache.clear()
        self.general_cache.clear()
        logger.info("All caches cleared")

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "analysis_cache": {
                "size": len(self.analysis_cache),
                "maxsize": self.analysis_cache.maxsize,
                "ttl": self.analysis_cache.ttl
            },
            "refine_cache": {
                "size": len(self.refine_cache),
                "maxsize": self.refine_cache.maxsize,
                "ttl": self.refine_cache.ttl
            },
            "general_cache": {
                "size": len(self.general_cache),
                "maxsize": self.general_cache.maxsize,
                "ttl": self.general_cache.ttl
            }
        }


# Global cache service instance
cache_service = CacheService()

# Import constants to avoid circular imports
from ..core import constants