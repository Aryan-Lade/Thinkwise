"""
Google Gemini AI service for analysis and refinement
"""

import json
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.errors import GeminiAPIError
from app.models.schemas import AnalysisResponse, RefineResponse

# Import constants to avoid circular imports
from ..core import constants

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self):
        """Initialize Gemini service."""
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_retries = settings.GEMINI_MAX_RETRIES

        # Configure generation settings
        self.generate_config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=constants.GEMINI_MAX_OUTPUT_TOKENS,
            top_p=constants.GEMINI_TOP_P,
            top_k=constants.GEMINI_TOP_K,
            response_mime_type="application/json",
        )

    async def analyze_decision(
        self,
        decision: str,
        details: Optional[str] = None,
        reasons: str = "",
        decision_type: Optional[str] = None
    ) -> AnalysisResponse:
        """
        Analyze a decision to identify blind spots.

        Args:
            decision: The decision being considered
            details: Additional details about the decision
            reasons: Main reasons for leaning a certain way
            decision_type: Type of decision (career, education, etc.)

        Returns:
            AnalysisResponse with blind spots analysis
        """
        try:
            # Build the prompt
            prompt = self._build_analysis_prompt(decision, details, reasons, decision_type)

            # Generate content with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=self.generate_config,
                    )

                    # Parse JSON response
                    if not response.text:
                        raise ValueError("Empty response from Gemini")

                    result_dict = json.loads(response.text)

                    # Validate with Pydantic
                    analysis_response = AnalysisResponse(**result_dict)

                    logger.info(f"Successfully analyzed decision (attempt {attempt + 1})")
                    return analysis_response

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Invalid JSON response from Gemini (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise GeminiAPIError(
                            f"Failed to parse Gemini response after {self.max_retries} attempts"
                        )
                    continue

                except Exception as e:
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise GeminiAPIError(f"Gemini API failed: {str(e)}")
                    continue

            # Should not reach here
            raise GeminiAPIError("Unexpected error in Gemini service")

        except Exception as e:
            logger.error(f"Error in analyze_decision: {e}")
            raise

    async def refine_analysis(
        self,
        session_id: str,
        answers: List[Dict[str, str]]
    ) -> RefineResponse:
        """
        Refine analysis based on user answers to questions.

        Args:
            session_id: Session identifier from initial analysis
            answers: List of user answers to questions

        Returns:
            RefineResponse with updated analysis
        """
        try:
            # Build the refinement prompt
            prompt = self._build_refine_prompt(session_id, answers)

            # Generate content with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=self.generate_config,
                    )

                    # Parse JSON response
                    if not response.text:
                        raise ValueError("Empty response from Gemini")

                    result_dict = json.loads(response.text)

                    # Validate with Pydantic
                    refine_response = RefineResponse(**result_dict)

                    logger.info(f"Successfully refined analysis (attempt {attempt + 1})")
                    return refine_response

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Invalid JSON response from Gemini (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise GeminiAPIError(
                            f"Failed to parse Gemini response after {self.max_retries} attempts"
                        )
                    continue

                except Exception as e:
                    logger.error(f"Gemini API error (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        raise GeminiAPIError(f"Gemini API failed: {str(e)}")
                    continue

            # Should not reach here
            raise GeminiAPIError("Unexpected error in Gemini service")

        except Exception as e:
            logger.error(f"Error in refine_analysis: {e}")
            raise

    def _build_analysis_prompt(
        self,
        decision: str,
        details: Optional[str],
        reasons: str,
        decision_type: Optional[str]
    ) -> str:
        """Build the analysis prompt for Gemini."""
        from app.prompts import ANALYSIS_SYSTEM_INSTRUCTION, ANALYSIS_FEW_SHOT_EXAMPLES

        prompt_parts = [
            ANALYSIS_SYSTEM_INSTRUCTION,
            "",
            "ANALYSIS REQUEST:",
            f"Decision: {decision}",
        ]

        if details and details.strip():
            prompt_parts.append(f"Details: {details}")

        prompt_parts.extend([
            f"Reasons for leaning: {reasons}",
        ])

        if decision_type:
            prompt_parts.append(f"Decision type: {decision_type}")

        prompt_parts.extend([
            "",
            ANALYSIS_FEW_SHOT_EXAMPLES,
            "",
            "IMPORTANT: Respond ONLY with valid JSON matching the schema.",
            "Do not include any explanatory text before or after the JSON.",
        ])

        return "\n".join(prompt_parts)

    def _build_refine_prompt(
        self,
        session_id: str,
        answers: List[Dict[str, str]]
    ) -> str:
        """Build the refinement prompt for Gemini."""
        from app.prompts import REFINE_SYSTEM_INSTRUCTION

        # Format answers for the prompt
        answers_text = "\n".join([
            f"- Question: {answer.get('question_id', 'Unknown')}"
            f"  Answer: {answer.get('answer', 'No answer provided')}"
            for answer in answers
        ])

        prompt_parts = [
            REFINE_SYSTEM_INSTRUCTION,
            "",
            "REFINEMENT REQUEST:",
            f"Session ID: {session_id}",
            "",
            "User's answers to previous questions:",
            answers_text,
            "",
            "",
            REFINE_SYSTEM_INSTRUCTION,
            "",
            "IMPORTANT: Respond ONLY with valid JSON matching the schema.",
            "Do not include any explanatory text before or after the JSON.",
        ]

        return "\n".join(prompt_parts)


# Create a singleton instance for use throughout the application
gemini_service = GeminiService()