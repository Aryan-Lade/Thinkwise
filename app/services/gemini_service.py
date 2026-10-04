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

        # Configure generation settings for structured JSON output
        self.analysis_config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=constants.GEMINI_MAX_OUTPUT_TOKENS,
            top_p=constants.GEMINI_TOP_P,
            top_k=constants.GEMINI_TOP_K,
            response_mime_type="application/json",
        )

        self.refine_config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=constants.GEMINI_MAX_OUTPUT_TOKENS,
            top_p=constants.GEMINI_TOP_P,
            top_k=constants.GEMINI_TOP_K,
            response_mime_type="application/json",
        )


    def _get_candidate_models(self) -> List[str]:
        """Return list of candidate models with fallbacks."""
        candidates = [self.model]
        for fallback in ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
            if fallback not in candidates:
                candidates.append(fallback)
        return candidates

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
        prompt = self._build_analysis_prompt(decision, details, reasons, decision_type)
        candidate_models = self._get_candidate_models()
        last_error = None

        for attempt in range(self.max_retries):
            for model_name in candidate_models:
                try:
                    logger.info(f"Attempting analysis with model {model_name} (attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=self.analysis_config,
                    )

                    if not response.text:
                        raise ValueError("Empty response from Gemini")

                    result_dict = json.loads(response.text)
                    analysis_response = AnalysisResponse(**result_dict)
                    logger.info(f"Successfully analyzed decision with {model_name}")
                    return analysis_response

                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_name} attempt {attempt + 1} failed: {e}")
                    # Try next candidate model

        raise GeminiAPIError(f"Failed to generate analysis after {self.max_retries} attempts: {last_error}")

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
        prompt = self._build_refine_prompt(session_id, answers)
        candidate_models = self._get_candidate_models()
        last_error = None

        for attempt in range(self.max_retries):
            for model_name in candidate_models:
                try:
                    logger.info(f"Attempting refinement with model {model_name} (attempt {attempt + 1})")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=self.refine_config,
                    )

                    if not response.text:
                        raise ValueError("Empty response from Gemini")

                    result_dict = json.loads(response.text)
                    refine_response = RefineResponse(**result_dict)
                    logger.info(f"Successfully refined analysis with {model_name}")
                    return refine_response

                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_name} refine attempt {attempt + 1} failed: {e}")
                    # Try next candidate model

        raise GeminiAPIError(f"Failed to refine analysis after {self.max_retries} attempts: {last_error}")

    def _build_analysis_prompt(
        self,
        decision: str,
        details: Optional[str],
        reasons: str,
        decision_type: Optional[str]
    ) -> str:
        """Build the analysis prompt for Gemini."""
        from app.prompts import (
            ANALYSIS_SYSTEM_INSTRUCTION,
            ANALYSIS_FEW_SHOT_EXAMPLES,
            WORKED_EXAMPLE_INTERNSHIP,
        )

        prompt_parts = [
            ANALYSIS_SYSTEM_INSTRUCTION,
            "",
            "REFERENCE WORKED EXAMPLE:",
            WORKED_EXAMPLE_INTERNSHIP,
            "",
            ANALYSIS_FEW_SHOT_EXAMPLES,
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
            f"- Question: {answer.get('question_id', 'Unknown')}\n"
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
            "IMPORTANT: Respond ONLY with valid JSON matching the schema.",
            "Do not include any explanatory text before or after the JSON.",
        ]

        return "\n".join(prompt_parts)


# Create a singleton instance for use throughout the application
gemini_service = GeminiService()