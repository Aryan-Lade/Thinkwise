"""
Refine endpoint for updating analysis based on user answers
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
import time

from app.core.config import get_settings
from app.core.errors import BlindSpotException, ValidationError
from app.core.logging import get_logger
from app.services.cache_service import cache_service
from app.services.gemini_service import gemini_service
from app.services.guard_service import guard_service
from app.services.session_service import session_service
from app.models.schemas import RefineRequest, RefineResponse

router = APIRouter()
logger = get_logger(__name__)


@router.post("/refine", response_model=RefineResponse)
async def refine_analysis(request: Request):
    """
    Refine analysis based on user answers to questions.

    Expected JSON payload:
    {
        "session_id": "string (required)",
        "answers": [
            {
                "question_id": "string (required)",
                "answer": "string (required)"
            }
        ]
    }
    """
    start_time = time.time()

    try:
        # Get request data
        data = await request.json()

        # Extract and validate fields
        session_id = data.get("session_id", "").strip()
        answers = data.get("answers", [])

        # Validate session_id
        if not session_id:
            raise ValidationError("Session ID is required")

        # Check if session exists
        if not session_service.session_exists(session_id):
            raise ValidationError(f"Session not found: {session_id}")

        # Validate answers
        if not isinstance(answers, list) or len(answers) == 0:
            raise ValidationError("Answers must be a non-empty list")

        for i, answer in enumerate(answers):
            if not isinstance(answer, dict):
                raise ValidationError(f"Answer {i} must be a dictionary")

            question_id = answer.get("question_id", "").strip()
            answer_text = answer.get("answer", "").strip()

            if not question_id:
                raise ValidationError(f"Answer {i}: question_id is required")
            if not answer_text:
                raise ValidationError(f"Answer {i}: answer is required")

        # Check cache for identical request (session_id + answers)
        # Convert answers to tuple of tuples for hashing
        answers_tuple = tuple(
            (answer["question_id"], answer["answer"])
            for answer in answers
        )

        cached_refine = cache_service.get_refine(session_id, answers_tuple)
        if cached_refine is not None:
            logger.info(f"Returning cached refine for session: {session_id}")
            return cached_refine

        # Perform refinement using Gemini service
        refine_result = await gemini_service.refine_analysis(
            session_id=session_id,
            answers=answers
        )

        # Apply guardrails to prevent directive language
        refine_result = guard_service.validate_and_guard_refine(refine_result)

        # Cache the result
        cache_service.set_refine(session_id, answers_tuple, refine_result)

        # Store refinement in session history
        session_service.append_to_history(
            session_id,
            {
                "type": "refinement",
                "timestamp": time.time(),
                "answers": answers,
                "refinement": refine_result.model_dump()
            }
        )

        # Update session with refinement data
        session_service.update_session(
            session_id,
            {
                "latest_refinement": refine_result.model_dump(),
                "refinement_count": session_service.get_session(session_id).get("data", {}).get("refinement_count", 0) + 1
            },
            merge=True
        )

        process_time = time.time() - start_time
        logger.info(f"Refinement completed in {process_time:.2f}s for session {session_id}")

        return refine_result

    except ValidationError as e:
        logger.warning(f"Validation error in refine: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except BlindSpotException as e:
        logger.error(f"BlindSpot error in refine: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in refine_analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Add OPTIONS handler for CORS preflight
@router.options("/refine")
async def refine_options():
    """Handle CORS preflight requests."""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )