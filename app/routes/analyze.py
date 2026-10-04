"""
Analysis endpoint for decision blind spot analysis
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
import time

from app.core import constants
from app.core.config import get_settings
from app.core.errors import BlindSpotException, ValidationError
from app.core.logging import get_logger
from app.services.cache_service import cache_service
from app.services.gemini_service import gemini_service
from app.services.guard_service import guard_service
from app.services.safety_service import safety_service
from app.services.session_service import session_service
from app.models.schemas import AnalysisResponse, DecisionType

router = APIRouter()
logger = get_logger(__name__)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_decision(request: Request):
    """
    Analyze a decision to identify blind spots in reasoning.

    Expected JSON payload:
    {
        "decision": "string (required)",
        "details": "string (optional)",
        "reasons": "string (required)",
        "decision_type": "string (optional, enum: career, education, financial, startup, personal, relationship, health, purchase, other)"
    }
    """
    start_time = time.time()

    try:
        # Get request data
        data = await request.json()

        # Extract and validate fields
        decision = data.get("decision", "").strip()
        details = data.get("details", "").strip() or None
        reasons = data.get("reasons", "").strip()
        decision_type = data.get("decision_type", "").strip() or None

        # Validate decision type if provided
        if decision_type and decision_type not in [dt.value for dt in DecisionType]:
            raise ValidationError(
                f"Invalid decision type: {decision_type}. "
                f"Must be one of: {[dt.value for dt in DecisionType]}"
            )

        # Validate required fields
        if not decision:
            raise ValidationError("Decision is required")
        if not reasons:
            raise ValidationError("Reasons for leaning are required")

        # Check input length limits
        if len(decision) > constants.MAX_DECISION_LENGTH:
            raise ValidationError(
                f"Decision too long. Maximum {constants.MAX_DECISION_LENGTH} characters allowed"
            )
        if details and len(details) > constants.MAX_DETAILS_LENGTH:
            raise ValidationError(
                f"Details too long. Maximum {constants.MAX_DETAILS_LENGTH} characters allowed"
            )
        if len(reasons) > constants.MAX_REASONS_LENGTH:
            raise ValidationError(
                f"Reasons too long. Maximum {constants.MAX_REASONS_LENGTH} characters allowed"
            )

        # Safety check - detect crisis indicators
        is_safe, safety_response = safety_service.validate_input_safety(
            decision, details, reasons
        )

        if not is_safe:
            # Return safety response instead of normal analysis
            logger.warning(f"Safety check failed for decision: {decision[:50]}...")
            # Create a safety-focused response
            session_id = session_service.create_session()

            safety_analysis = AnalysisResponse(
                session_id=session_id,
                round=1,
                decision_restated=decision,
                reasoning_map=AnalysisResponse.model_fields["reasoning_map"].default_factory(),
                overlooked_factors=[],
                assumptions=[],
                conflicts=[],
                stakeholders=[],
                alternatives_not_considered=[],
                possible_biases=[],
                questions=[],
                what_would_change_your_mind=None,
                reversibility_note=None,
                safety_flag=True,
                guard_notes=["Safety check triggered - crisis indicators detected"]
            )

            # In a real implementation, we might return the safety response differently
            # For now, we'll return the analysis with safety_flag=True
            # The frontend should handle displaying the safety message

            # Store the safety response in session for potential use
            session_service.update_session(
                session_id,
                {"safety_response": safety_response},
                merge=True
            )

            process_time = time.time() - start_time
            logger.info(f"Safety response generated in {process_time:.2f}s")
            return safety_analysis

        # Check cache for identical request
        cached_analysis = cache_service.get_analysis(decision, details, reasons, decision_type)
        if cached_analysis is not None:
            logger.info(f"Returning cached analysis for decision: {decision[:30]}...")
            return cached_analysis

        # Create or get session
        session_id = session_service.create_session()

        # Perform analysis using Gemini service
        analysis = await gemini_service.analyze_decision(
            decision=decision,
            details=details,
            reasons=reasons,
            decision_type=decision_type
        )

        # Ensure session_id is set
        analysis.session_id = session_id

        # Apply guardrails to prevent directive language
        analysis = guard_service.validate_and_guard_analysis(analysis)

        # Cache the result
        cache_service.set_analysis(decision, details, reasons, decision_type, analysis)

        # Store analysis in session history
        session_service.append_to_history(
            session_id,
            {
                "type": "initial_analysis",
                "timestamp": time.time(),
                "analysis": analysis.model_dump()
            }
        )

        process_time = time.time() - start_time
        logger.info(f"Analysis completed in {process_time:.2f}s for session {session_id}")

        return analysis

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except BlindSpotException as e:
        logger.error(f"BlindSpot error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze_decision: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )



# Add OPTIONS handler for CORS preflight
@router.options("/analyze")
async def analyze_options():
    """Handle CORS preflight requests."""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )