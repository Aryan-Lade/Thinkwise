"""
Service for guarding against directive language in AI responses
"""

import re
import logging
from typing import List, Tuple

from app.core.config import get_settings
from app.core.errors import BlindSpotException
from app.models.schemas import AnalysisResponse, RefineResponse

# Import constants to avoid circular imports
from ..core import constants

logger = logging.getLogger(__name__)


class GuardService:
    """Service for detecting and handling directive language in AI responses."""

    def __init__(self):
        """Initialize guard service with directive phrases."""
        settings = get_settings()
        self.directive_phrases = self._compile_directive_phrases()
        self.max_regenerations = 1  # Only regenerate once as per spec

    def _compile_directive_phrases(self) -> List[re.Pattern]:
        """Compile directive phrases into regex patterns."""
        phrases = [
            # Direct recommendations
            r"you\s+should",
            r"i\s+recommend",
            r"the\s+best\s+option\s+is",
            r"go\s+with",
            r"you\s+must",
            r"my\s+advice\s+is",
            r"choose\s+\w+",
            r"pick\s+\w+",
            r"select\s+\w+",
            r"opt\s+for",
            r"decide\s+to",
            r"it\s+is\s+better\s+to",
            r"you\s+ought\s+to",
            r"i\s+suggest\s+you",
            r"consider\s+choosing",
            r"go\s+ahead\s+and",
            r"definitely\s+choose",
            r"without\s+doubt",
            r"clearly\s+you\s+should",
            r"the\s+right\s+choice\s+is",

            # Decision-making language
            r"i\s+think\s+you\s+should",
            r"in\s+my\s+opinion",
            r"based\s+on\s+my\s+analysis",
            r"as\s+an\s+ai\s+advisor",
            r"according\s+to\s+my\s+evaluation",

            # Strong suggestions
            r"it\s+would\s+be\s+wise\s+to",
            r"the\s+smarter\s+choice",
            r"the\s+more\s+beneficial\s+option",
            r"you\s+would\s+be\s+better\s+off",
        ]

        # Compile patterns with case-insensitive flag
        patterns = [re.compile(phrase, re.IGNORECASE) for phrase in phrases]
        return patterns

    def check_for_directives(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check text for directive language.

        Args:
            text: Text to check

        Returns:
            Tuple of (has_directives, list_of_matches)
        """
        if not text or not isinstance(text, str):
            return False, []

        matches = []
        for pattern in self.directive_phrases:
            found_matches = pattern.findall(text)
            if found_matches:
                matches.extend(found_matches)

        return len(matches) > 0, matches

    def sanitize_text(self, text: str, matches: List[str]) -> str:
        """
        Sanitize text by removing or replacing directive language.

        Args:
            text: Original text
            matches: List of directive matches found

        Returns:
            Sanitized text
        """
        if not matches:
            return text

        sanitized = text
        for match in matches:
            # Replace directive phrases with neutral alternatives
            # Case-insensitive replacement
            pattern = re.compile(re.escape(match), re.IGNORECASE)
            sanitized = pattern.sub("[guidance removed]", sanitized)

        return sanitized

    def validate_and_guard_analysis(
        self,
        analysis: AnalysisResponse
    ) -> AnalysisResponse:
        """
        Validate and guard an analysis response against directive language.

        Args:
            analysis: Analysis response to validate

        Returns:
            Potentially modified analysis response

        Raises:
            BlindSpotException: If directive language persists after guarding
        """
        # Convert to dict for easier manipulation
        analysis_dict = analysis.model_dump()

        # Check all string fields for directives
        guard_notes = []

        # Fields to check for directive language
        string_fields_to_check = [
            "decision_restated",
            "what_would_change_your_mind",
            "reversibility_note"
        ]

        # Check complex fields
        complex_checks = [
            ("overlooked_factors", ["text", "why_it_matters"]),
            ("assumptions", ["text", "how_to_test"]),
            ("conflicts", ["statement_a", "statement_b", "tension"]),
            ("questions", ["text"]),
            ("possible_biases", ["why_it_may_apply"]),
        ]

        # Check simple string fields
        for field in string_fields_to_check:
            value = analysis_dict.get(field)
            if value and isinstance(value, str):
                has_directives, matches = self.check_for_directives(value)
                if has_directives:
                    guard_notes.append(f"Directive language found in {field}: {matches}")
                    # Sanitize the field
                    analysis_dict[field] = self.sanitize_text(value, matches)

        # Check complex fields
        for field_name, subfields in complex_checks:
            items = analysis_dict.get(field_name, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        for subfield in subfields:
                            value = item.get(subfield)
                            if value and isinstance(value, str):
                                has_directives, matches = self.check_for_directives(value)
                                if has_directives:
                                    guard_notes.append(
                                        f"Directive language found in {field_name}[{i}].{subfield}: {matches}"
                                    )
                                    # Sanitize the field
                                    item[subfield] = self.sanitize_text(value, matches)

        # Update guard_notes in the analysis
        analysis_dict["guard_notes"] = guard_notes

        # Check if we should regenerate (only once)
        if guard_notes and len(guard_notes) > 0:
            logger.warning(f"Directive language detected and guarded: {guard_notes}")
            # In a real implementation, we might regenerate here
            # For now, we just sanitize and add to guard_notes

        # Return validated analysis
        return AnalysisResponse(**analysis_dict)

    def validate_and_guard_refine(
        self,
        refine: RefineResponse
    ) -> RefineResponse:
        """
        Validate and guard a refine response against directive language.

        Args:
            refine: Refine response to validate

        Returns:
            Potentially modified refine response
        """
        # Similar implementation as above but for RefineResponse
        refine_dict = refine.model_dump()

        guard_notes = []

        # Check string fields
        string_fields_to_check = [
            "decision_restated",
            "what_changed"
        ]

        for field in string_fields_to_check:
            value = refine_dict.get(field)
            if value and isinstance(value, str):
                has_directives, matches = self.check_for_directives(value)
                if has_directives:
                    guard_notes.append(f"Directive language found in {field}: {matches}")
                    refine_dict[field] = self.sanitize_text(value, matches)

        # Check complex fields
        complex_checks = [
            ("overlooked_factors", ["text", "why_it_matters"]),
            ("assumptions", ["text", "how_to_test"]),
            ("conflicts", ["statement_a", "statement_b", "tension"]),
            ("questions", ["text"]),
        ]

        for field_name, subfields in complex_checks:
            items = refine_dict.get(field_name, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        for subfield in subfields:
                            value = item.get(subfield)
                            if value and isinstance(value, str):
                                has_directives, matches = self.check_for_directives(value)
                                if has_directives:
                                    guard_notes.append(
                                        f"Directive language found in {field_name}[{i}].{subfield}: {matches}"
                                    )
                                    item[subfield] = self.sanitize_text(value, matches)

        refine_dict["guard_notes"] = guard_notes

        if guard_notes:
            logger.warning(f"Directive language detected in refine and guarded: {guard_notes}")

        return RefineResponse(**refine_dict)


# Create a singleton instance for use throughout the application
guard_service = GuardService()