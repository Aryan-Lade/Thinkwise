"""
Safety service for detecting crisis indicators and providing support
"""

import re
import logging
from typing import List, Tuple, Optional

from app.core.config import get_settings
from app.core.errors import BlindSpotException

logger = logging.getLogger(__name__)


class SafetyService:
    """Service for detecting crisis indicators and providing safety responses."""

    def __init__(self):
        """Initialize safety service with crisis patterns."""
        self.crisis_patterns = self._compile_crisis_patterns()
        self.safety_responses = self._load_safety_responses()

    def _compile_crisis_patterns(self) -> List[re.Pattern]:
        """Compile crisis indicator patterns."""
        # Patterns indicating potential self-harm, crisis, or harmful intent
        crisis_phrases = [
            # Self-harm / suicide ideation
            r"kill\s+myself",
            r"suicide",
            r"end\s+it\s+all",
            r"want\s+to\s+die",
            r"better\s+off\s+dead",
            r"hurt\s+myself",
            r"self[\s\-]harm",
            r"cut\s+myself",
            r"overdose",
            r"jump\s+off",
            r"hang\s+myself",

            # Violence / harm to others
            r"kill\s+them",
            r"hurt\s+someone",
            r"violence",
            r"attack",
            r"harm\s+others",
            r"revenge",
            r"get\s+back\s+at",

            # Extreme distress / hopelessness
            r"can'?t\s+go\s+on",
            r"no\s+point\s+in\s+living",
            r"hopeless",
            r"worthless",
            r"nobody\s+cares",
            r"everyone\s+would\s+be\s+better\s+without\s+me",

            # Substance abuse crisis
            r"need\s+more\s+drugs",
            r"can'?t\s+stop\s+drinking",
            r"overdose\s+on\s+pills",

            # Abuse situations
            r"being\s+abused",
            r"domestic\s+violence",
            r"someone\s+is\s+hitting\s+me",
            r"can'?t\s+leave\s+the\s+relationship",
        ]

        # Compile patterns with case-insensitive flag
        patterns = [re.compile(phrase, re.IGNORECASE) for phrase in crisis_phrases]
        return patterns

    def _load_safety_responses(self) -> dict:
        """Load safety response messages."""
        return {
            "crisis_detected": (
                "I'm really concerned about what you've shared. Your safety and wellbeing are the most important things right now. "
                "If you're in immediate danger or feeling unsafe, please reach out for help right away. "
                "You don't have to go through this alone. "
                "Consider contacting a trusted friend, family member, or professional support service. "
                "If you're in the US, you can call or text 988 (Suicide & Crisis Lifeline) or text 'HELLO' to 741741 (Crisis Text Line). "
                "If you're elsewhere, please look up local emergency services or crisis hotlines in your country. "
                "Your life matters, and there are people who want to help you through this."
            ),
            "general_concern": (
                "Thank you for sharing your thoughts with me. It sounds like you're going through a challenging time. "
                "While I'm here to help with decision-making, I'm not equipped to provide the kind of support you might need right now. "
                "Please consider reaching out to someone you trust - a friend, family member, counselor, or other support person. "
                "You deserve support and care during difficult decisions."
            )
        }

    def check_for_crisis_indicators(
        self,
        text: str
    ) -> Tuple[bool, List[str]]:
        """
        Check text for crisis indicators.

        Args:
            text: Text to check (user input)

        Returns:
            Tuple of (has_crisis, list_of_matched_patterns)
        """
        if not text or not isinstance(text, str):
            return False, []

        matches = []
        for pattern in self.crisis_patterns:
            found_matches = pattern.findall(text)
            if found_matches:
                matches.extend(found_matches)

        return len(matches) > 0, matches

    def get_safety_response(self, crisis_type: str = "crisis_detected") -> str:
        """
        Get appropriate safety response.

        Args:
            crisis_type: Type of crisis detected

        Returns:
            Safety response message
        """
        return self.safety_responses.get(
            crisis_type,
            self.safety_responses["general_concern"]
        )

    def validate_input_safety(
        self,
        decision: str,
        details: Optional[str] = None,
        reasons: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate user input for safety concerns.

        Args:
            decision: The decision being considered
            details: Additional details about the decision
            reasons: Main reasons for leaning a certain way

        Returns:
            Tuple of (is_safe, safety_response_if_unsafe)
        """
        # Combine all text to check
        full_text = f"{decision} {details or ''} {reasons}".strip()

        has_crisis, matches = self.check_for_crisis_indicators(full_text)

        if has_crisis:
            logger.warning(f"Crisis indicators detected in user input: {matches}")
            safety_response = self.get_safety_response("crisis_detected")
            return False, safety_response

        return True, None

    def is_safe_to_proceed(
        self,
        decision: str,
        details: Optional[str] = None,
        reasons: str = ""
    ) -> bool:
        """
        Check if it's safe to proceed with normal analysis.

        Args:
            decision: The decision being considered
            details: Additional details about the decision
            reasons: Main reasons for leaning a certain way

        Returns:
            True if safe to proceed, False if safety concerns detected
        """
        is_safe, _ = self.validate_input_safety(decision, details, reasons)
        return is_safe


# Global safety service instance
safety_service = SafetyService()

# Import constants to avoid circular imports
from ..core import constants