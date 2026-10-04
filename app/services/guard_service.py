"""
Service for guarding against directive language in AI responses
"""

import logging
import re
from typing import List, Tuple

from app.models.schemas import AnalysisResponse, RefineResponse

# Import constants to avoid circular imports

logger = logging.getLogger(__name__)


class GuardService:
    """Service for detecting and handling directive language in AI responses."""

    def __init__(self):
        """Initialize guard service with directive phrases."""
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
            r"(?:you|i)\s+must",
            r"my\s+advi[cs]e\s+is",
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
            pattern = re.compile(re.escape(match), re.IGNORECASE)
            sanitized = pattern.sub("[guidance removed]", sanitized)

        return sanitized

    def validate_and_guard_analysis(
        self, analysis: AnalysisResponse
    ) -> AnalysisResponse:
        """
        Validate and guard an analysis response against directive language.
        """
        analysis_dict = analysis.model_dump()
        guard_notes = []

        string_fields_to_check = [
            "decision_restated",
            "what_would_change_your_mind",
            "reversibility_note",
        ]

        # Check simple string fields
        for field in string_fields_to_check:
            value = analysis_dict.get(field)
            if value and isinstance(value, str):
                has_directives, matches = self.check_for_directives(value)
                if has_directives:
                    guard_notes.append(
                        f"Directive language found in {field}: {matches}"
                    )
                    analysis_dict[field] = self.sanitize_text(value, matches)

        # Check reasoning map
        rm = analysis_dict.get("reasoning_map")
        if isinstance(rm, dict):
            for rm_field in [
                "stated_factors",
                "stated_reasons",
                "most_visible_factors",
                "thin_or_missing_areas",
            ]:
                factors = rm.get(rm_field, [])
                if isinstance(factors, list):
                    for i, factor in enumerate(factors):
                        if isinstance(factor, str):
                            has_directives, matches = self.check_for_directives(factor)
                            if has_directives:
                                guard_notes.append(
                                    f"Directive language found in reasoning_map.{rm_field}[{i}]: {matches}"
                                )
                                factors[i] = self.sanitize_text(factor, matches)

        # Check complex fields
        complex_checks = [
            ("overlooked_factors", ["text", "why_it_matters"]),
            ("assumptions", ["text", "how_to_test"]),
            ("conflicts", ["statement_a", "statement_b", "tension"]),
            ("questions", ["text"]),
            ("possible_biases", ["why_it_may_apply"]),
        ]

        for field_name, subfields in complex_checks:
            items = analysis_dict.get(field_name, [])
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict):
                        for subfield in subfields:
                            value = item.get(subfield)
                            if value and isinstance(value, str):
                                has_directives, matches = self.check_for_directives(
                                    value
                                )
                                if has_directives:
                                    guard_notes.append(
                                        f"Directive language found in {field_name}[{i}].{subfield}: {matches}"
                                    )
                                    item[subfield] = self.sanitize_text(value, matches)

        analysis_dict["guard_notes"] = guard_notes

        if guard_notes:
            logger.warning(f"Directive language detected and guarded: {guard_notes}")

        return AnalysisResponse(**analysis_dict)

    def validate_and_guard_refine(self, refine: RefineResponse) -> RefineResponse:
        """
        Validate and guard a refine response against directive language.
        """
        refine_dict = refine.model_dump()
        guard_notes = []

        string_fields_to_check = ["decision_restated", "what_changed"]

        for field in string_fields_to_check:
            value = refine_dict.get(field)
            if value and isinstance(value, str):
                has_directives, matches = self.check_for_directives(value)
                if has_directives:
                    guard_notes.append(
                        f"Directive language found in {field}: {matches}"
                    )
                    refine_dict[field] = self.sanitize_text(value, matches)

        # Check reasoning map
        rm = refine_dict.get("reasoning_map")
        if isinstance(rm, dict):
            for rm_field in [
                "stated_factors",
                "stated_reasons",
                "most_visible_factors",
                "thin_or_missing_areas",
            ]:
                factors = rm.get(rm_field, [])
                if isinstance(factors, list):
                    for i, factor in enumerate(factors):
                        if isinstance(factor, str):
                            has_directives, matches = self.check_for_directives(factor)
                            if has_directives:
                                guard_notes.append(
                                    f"Directive language found in reasoning_map.{rm_field}[{i}]: {matches}"
                                )
                                factors[i] = self.sanitize_text(factor, matches)

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
                                has_directives, matches = self.check_for_directives(
                                    value
                                )
                                if has_directives:
                                    guard_notes.append(
                                        f"Directive language found in {field_name}[{i}].{subfield}: {matches}"
                                    )
                                    item[subfield] = self.sanitize_text(value, matches)

        refine_dict["guard_notes"] = guard_notes

        if guard_notes:
            logger.warning(
                f"Directive language detected in refine and guarded: {guard_notes}"
            )

        return RefineResponse(**refine_dict)


# Create a singleton instance for use throughout the application
guard_service = GuardService()
