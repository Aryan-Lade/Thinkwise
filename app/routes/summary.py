"""
Summary endpoint for generating thinking summary
"""

import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.errors import BlindSpotException, ValidationError
from app.core.logging import get_logger
from app.models.schemas import (
    AnalysisResponse,
    DecisionType,
    RefineResponse,
    SummaryResponse,
)
from app.services.session_service import session_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: Request):
    """
    Generate a thinking summary for the user's decision analysis.

    Expected JSON payload:
    {
        "session_id": "string (required)"
    }
    """
    start_time = time.time()

    try:
        # Get request data
        data = await request.json()

        # Extract and validate fields
        session_id = data.get("session_id", "").strip()

        # Validate session_id
        if not session_id:
            raise ValidationError("Session ID is required")

        # Check if session exists
        session_data = session_service.get_session(session_id)
        if not session_data:
            raise ValidationError(f"Session not found: {session_id}")

        # Extract data from session
        session_info = session_data.get("data", {})
        history = session_data.get("history", [])

        # Find the latest analysis and refinement
        latest_analysis = None
        latest_refinement = None
        user_answers = []

        # Go through history in reverse to find latest items
        for entry in reversed(history):
            if entry.get("type") == "initial_analysis" and latest_analysis is None:
                # Reconstruct analysis from stored data
                from app.models.schemas import AnalysisResponse

                latest_analysis = AnalysisResponse(**entry["analysis"])
            elif entry.get("type") == "refinement" and latest_refinement is None:
                # Reconstruct refinement from stored data
                from app.models.schemas import RefineResponse

                latest_refinement = RefineResponse(**entry["refinement"])
                user_answers = entry.get("answers", [])

            # Break early if we have both
            if latest_analysis and latest_refinement is not None:
                break

        # If we don't have a refinement but have analysis, use empty answers
        if latest_analysis and not latest_refinement:
            latest_refinement = None  # Will handle in summary generation
            # Extract answers from any refinement entries if they exist
            for entry in history:
                if entry.get("type") == "refinement":
                    user_answers.extend(entry.get("answers", []))

        if not latest_analysis:
            raise ValidationError("No analysis found in session")

        # Generate thinking summary
        thinking_summary = _generate_thinking_summary(
            latest_analysis=latest_analysis,
            latest_refinement=latest_refinement,
            user_answers=user_answers,
            session_info=session_info,
        )

        # Determine decision type from session info or default
        decision_type_str = session_info.get("decision_type")
        decision_type = None
        if decision_type_str:
            try:
                decision_type = DecisionType(decision_type_str)
            except ValueError:
                decision_type = None

        # Create summary response
        summary = SummaryResponse(
            session_id=session_id,
            decision=latest_analysis.decision_restated,
            details=session_info.get("details"),
            reasons=session_info.get("reasons", ""),
            decision_type=decision_type,
            reasoning_map=latest_analysis.reasoning_map,
            overlooked_factors=latest_analysis.overlooked_factors,
            assumptions=latest_analysis.assumptions,
            conflicts=latest_analysis.conflicts,
            questions=latest_analysis.questions,
            answers=user_answers,
            thinking_summary=thinking_summary,
            created_at=datetime.fromtimestamp(
                session_data.get("created_at", time.time())
            ),
        )

        # Store summary in session history
        session_service.append_to_history(
            session_id,
            {
                "type": "summary_generated",
                "timestamp": time.time(),
                "summary": summary.model_dump(),
            },
        )

        process_time = time.time() - start_time
        logger.info(
            f"Summary generated in {process_time:.2f}s for session {session_id}"
        )

        return summary

    except ValidationError as e:
        logger.warning(f"Validation error in summary: {e.message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except BlindSpotException as e:
        logger.error(f"BlindSpot error in summary: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in generate_summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def _generate_thinking_summary(
    latest_analysis: "AnalysisResponse",
    latest_refinement: "RefineResponse",
    user_answers: list,
    session_info: dict,
) -> str:
    """
    Generate a formatted thinking summary for the user.

    Args:
        latest_analysis: The initial analysis response
        latest_refinement: The latest refinement response (if any)
        user_answers: List of user answers to questions
        session_info: Session metadata

    Returns:
        Formatted thinking summary string
    """
    summary_parts = []

    # Header
    summary_parts.append("# My Thinking Summary")
    summary_parts.append("")
    summary_parts.append("This document captures your decision-making process,")
    summary_parts.append("the insights gained through reflection,")
    summary_parts.append("and open questions for further consideration.")
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")

    # Decision overview
    summary_parts.append("## Your Decision")
    summary_parts.append("")
    summary_parts.append(f"**Decision:** {latest_analysis.decision_restated}")
    if session_info.get("details"):
        summary_parts.append(f"**Details:** {session_info['details']}")
    summary_parts.append(
        f"**Your reasons:** {session_info.get('reasons', 'Not provided')}"
    )
    if session_info.get("decision_type"):
        summary_parts.append(f"**Decision type:** {session_info['decision_type']}")
    summary_parts.append("")

    # Reasoning map
    summary_parts.append("## What You're Focusing On")
    summary_parts.append("")
    if latest_analysis.reasoning_map.stated_factors:
        summary_parts.append("**Factors you mentioned:**")
        for factor in latest_analysis.reasoning_map.stated_factors:
            summary_parts.append(f"- {factor}")
        summary_parts.append("")

    if latest_analysis.reasoning_map.stated_reasons:
        summary_parts.append("**Your stated reasons:**")
        for reason in latest_analysis.reasoning_map.stated_reasons:
            summary_parts.append(f"- {reason}")
        summary_parts.append("")

    if latest_analysis.reasoning_map.most_visible_factors:
        summary_parts.append("**What dominates your attention:**")
        for factor in latest_analysis.reasoning_map.most_visible_factors:
            summary_parts.append(f"- {factor}")
        summary_parts.append("")

    if latest_analysis.reasoning_map.thin_or_missing_areas:
        summary_parts.append("**Areas that are less developed in your thinking:**")
        for area in latest_analysis.reasoning_map.thin_or_missing_areas:
            summary_parts.append(f"- {area}")
        summary_parts.append("")

    # Overlooked factors
    if latest_analysis.overlooked_factors:
        summary_parts.append("## What Might Be Missing")
        summary_parts.append("")
        for factor in latest_analysis.overlooked_factors:
            summary_parts.append(f"### {factor.text}")
            summary_parts.append("")
            summary_parts.append(f"*Why this matters:* {factor.why_it_matters}")
            summary_parts.append("")

    # Assumptions
    if latest_analysis.assumptions:
        summary_parts.append("## Assumptions to Examine")
        summary_parts.append("")
        for assumption in latest_analysis.assumptions:
            summary_parts.append(f"### {assumption.text}")
            summary_parts.append("")
            summary_parts.append(f"*How to test this:* {assumption.how_to_test}")
            summary_parts.append("")

    # Conflicts
    if latest_analysis.conflicts:
        summary_parts.append("## Where Your Reasoning May Pull Against Itself")
        summary_parts.append("")
        for conflict in latest_analysis.conflicts:
            summary_parts.append("### Tension between two statements:")
            summary_parts.append("")
            summary_parts.append(f"> {conflict.statement_a}")
            summary_parts.append(f"> {conflict.statement_b}")
            summary_parts.append("")
            summary_parts.append(f"*Why this tension exists:* {conflict.tension}")
            summary_parts.append("")

    # Questions and answers (if refinement exists)
    if latest_refinement and user_answers:
        summary_parts.append("## Your Reflections")
        summary_parts.append("")
        summary_parts.append("Based on your answers to the reflection questions:")
        summary_parts.append("")

        # Create a map of question_id to answer for easy lookup
        answer_map = {
            answer["question_id"]: answer["answer"] for answer in user_answers
        }

        # Show questions from latest refinement with user answers
        for question in latest_refinement.questions:
            answer = answer_map.get(question.id, "No answer recorded")
            summary_parts.append(f"### {question.theme.title()}: {question.text}")
            summary_parts.append("")
            summary_parts.append(f"**Your response:** {answer}")
            summary_parts.append("")

            # Show what changed if available
            if (
                hasattr(latest_refinement, "what_changed")
                and latest_refinement.what_changed
            ):
                summary_parts.append(
                    f"*What shifted in your thinking:* {latest_refinement.what_changed}"
                )
                summary_parts.append("")

    elif latest_analysis.questions:
        summary_parts.append("## Questions for Further Reflection")
        summary_parts.append("")
        summary_parts.append(
            "Consider these open-ended questions to deepen your thinking:"
        )
        summary_parts.append("")
        for question in latest_analysis.questions:
            summary_parts.append(f"### {question.theme.title()}: {question.text}")
            summary_parts.append("")

    # Additional insights
    mind_change = getattr(
        latest_refinement, "what_would_change_your_mind", None
    ) or getattr(latest_analysis, "what_would_change_your_mind", None)
    if mind_change:
        summary_parts.append("## What Would Change Your Mind?")
        summary_parts.append("")
        summary_parts.append(mind_change)
        summary_parts.append("")

    rev_note = getattr(latest_refinement, "reversibility_note", None) or getattr(
        latest_analysis, "reversibility_note", None
    )
    if rev_note:
        summary_parts.append("## Thoughts on Reversibility")
        summary_parts.append("")
        summary_parts.append(rev_note)
        summary_parts.append("")

    # Possible biases (tentative)
    if latest_analysis.possible_biases:
        summary_parts.append("## Possible Thinking Patterns to Notice")
        summary_parts.append("")
        summary_parts.append(
            "*(These are offered tentatively as patterns to reflect on, not as conclusions)*"
        )
        summary_parts.append("")
        for bias in latest_analysis.possible_biases:
            summary_parts.append(f"### {bias.name}")
            summary_parts.append("")
            summary_parts.append(f"*Why this may apply:* {bias.why_it_may_apply}")
            summary_parts.append("")

    # Footer
    summary_parts.append("---")
    summary_parts.append("")
    summary_parts.append(
        "**Remember:** This tool asks questions to help you think more deeply."
    )
    summary_parts.append("The decision belongs entirely to you.")
    summary_parts.append("")
    summary_parts.append(
        f"*Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
    )

    return "\n".join(summary_parts)


# Add OPTIONS handler for CORS preflight
@router.options("/summary")
async def summary_options():
    """Handle CORS preflight requests."""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )
