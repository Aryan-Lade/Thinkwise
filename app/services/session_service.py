"""
Session service for managing user sessions
"""

import logging
from typing import Dict, Optional
from uuid import uuid4

from cachetools import TTLCache
from app.core.config import get_settings
from app.core.errors import BlindSpotException

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions with TTL cache."""

    def __init__(self):
        """Initialize session service."""
        settings = get_settings()
        # Cache for storing session data
        self._cache = TTLCache(
            maxsize=1000,  # Maximum number of sessions
            ttl=settings.CACHE_TTL * settings.SESSION_TTL_HOURS  # Convert hours to seconds
        )
        self.settings = settings

    def create_session(self) -> str:
        """
        Create a new session.

        Returns:
            Session ID
        """
        session_id = str(uuid4())
        # Initialize empty session data
        self._cache[session_id] = {
            "created_at": self._get_current_timestamp(),
            "data": {},
            "analysis_history": [],
        }
        logger.info(f"Created new session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data if found, None otherwise
        """
        session_data = self._cache.get(session_id)
        if session_data is None:
            logger.warning(f"Session not found: {session_id}")
            return None

        logger.debug(f"Retrieved session: {session_id}")
        return session_data

    def update_session(
        self,
        session_id: str,
        data: Dict,
        merge: bool = True
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            data: Data to store
            merge: Whether to merge with existing data or replace

        Returns:
            True if successful, False if session not found
        """
        session_data = self._cache.get(session_id)
        if session_data is None:
            logger.warning(f"Cannot update non-existent session: {session_id}")
            return False

        if merge:
            session_data["data"].update(data)
        else:
            session_data["data"] = data

        session_data["updated_at"] = self._get_current_timestamp()
        logger.debug(f"Updated session: {session_id}")
        return True

    def append_to_history(
        self,
        session_id: str,
        entry: Dict
    ) -> bool:
        """
        Append an entry to session history.

        Args:
            session_id: Session identifier
            entry: History entry to append

        Returns:
            True if successful, False if session not found
        """
        session_data = self._cache.get(session_id)
        if session_data is None:
            logger.warning(f"Cannot append to history for non-existent session: {session_id}")
            return False

        if "history" not in session_data:
            session_data["history"] = []

        session_data["history"].append(entry)
        session_data["updated_at"] = self._get_current_timestamp()
        logger.debug(f"Appended to history for session: {session_id}")
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False if session not found
        """
        if session_id in self._cache:
            del self._cache[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        else:
            logger.warning(f"Cannot delete non-existent session: {session_id}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        return session_id in self._cache

    def get_session_count(self) -> int:
        """
        Get the number of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self._cache)

    def _get_current_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global session service instance
session_service = SessionService()

# Import constants to avoid circular imports
from ..core import constants