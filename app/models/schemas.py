"""
Pydantic models and schemas for Blind Spot application
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator
from typing_extensions import Annotated

# Import constants to avoid circular imports
from ..core import constants

# Type aliases for constrained strings
DecisionText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=constants.MIN_DECISION_LENGTH,
        max_length=constants.MAX_DECISION_LENGTH,
    ),
]

DetailsText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=constants.MAX_DETAILS_LENGTH),
]

ReasonsText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=constants.MIN_REASONS_LENGTH,
        max_length=constants.MAX_REASONS_LENGTH,
    ),
]


class DecisionType(str, Enum):
    """Decision type enumeration."""

    CAREER = "career"
    EDUCATION = "education"
    FINANCIAL = "financial"
    STARTUP = "startup"
    PERSONAL = "personal"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    PURCHASE = "purchase"
    OTHER = "other"


class StripModel(BaseModel):
    """Base model that automatically strips whitespace from all string fields."""

    model_config = ConfigDict(str_strip_whitespace=True)


class ReasoningMap(StripModel):
    """Reasoning map extracted from user input."""

    stated_factors: List[str] = Field(
        description="Details/factors the user explicitly mentioned"
    )
    stated_reasons: List[str] = Field(
        description="Main reasons the user gave for their lean"
    )
    most_visible_factors: List[str] = Field(
        description="What dominates the user's attention"
    )
    thin_or_missing_areas: List[str] = Field(
        description="Areas that are absent or thin in user's input"
    )

    @field_validator(
        "stated_factors",
        "stated_reasons",
        "most_visible_factors",
        "thin_or_missing_areas",
        mode="before",
    )
    @classmethod
    def strip_list_items(cls, v):
        if isinstance(v, list):
            return [x.strip() if isinstance(x, str) else x for x in v]
        return v


class OverlookedFactor(StripModel):
    """An overlooked factor in the user's reasoning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(description="Description of the overlooked factor")
    why_it_matters: str = Field(description="Why this factor matters for the decision")


class Assumption(StripModel):
    """An unstated assumption behind the user's stated reasons."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(description="The assumption")
    how_to_test: str = Field(description="How to test this assumption")


class Conflict(StripModel):
    """A conflict/tension within the user's own reasoning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    statement_a: str = Field(description="First statement from user input")
    statement_b: str = Field(description="Second statement from user input")
    tension: str = Field(description="Why these statements may pull against each other")


class Stakeholder(StripModel):
    """A stakeholder affected by the decision."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description="Stakeholder name or role")
    concern: str = Field(description="What this stakeholder might care about")


class Alternative(StripModel):
    """An alternative not considered by the user."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(description="Description of the alternative")


class Bias(StripModel):
    """A possible cognitive bias that may be affecting reasoning."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description="Name of the bias")
    why_it_may_apply: str = Field(
        description="Why this bias may apply to this decision"
    )


class Question(StripModel):
    """A thoughtful, open-ended question for reflection."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    theme: str = Field(description="Theme grouping for the question")
    text: str = Field(description="The question text")


class AnalysisResponse(StripModel):
    """Response from the analysis endpoint."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    round: int = Field(default=1, description="Analysis round number")
    decision_restated: str = Field(description="User's decision restated for clarity")
    reasoning_map: ReasoningMap
    overlooked_factors: List[OverlookedFactor] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    stakeholders: List[Stakeholder] = Field(default_factory=list)
    alternatives_not_considered: List[Alternative] = Field(default_factory=list)
    possible_biases: List[Bias] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)
    what_would_change_your_mind: Optional[str] = Field(
        default=None, description="What information would change the user's mind"
    )
    reversibility_note: Optional[str] = Field(
        default=None, description="Note about decision reversibility"
    )
    safety_flag: bool = Field(
        default=False, description="True if safety concerns were detected"
    )
    guard_notes: List[str] = Field(
        default_factory=list, description="Notes from safety guards"
    )


class RefineRequest(StripModel):
    """Request for refining analysis based on user answers."""

    session_id: str
    answers: List[dict]  # List of {question_id: str, answer: str}


class RefineResponse(StripModel):
    """Response from the refine endpoint."""

    session_id: str
    round: int = Field(description="Analysis round number")
    decision_restated: str
    reasoning_map: ReasoningMap
    overlooked_factors: List[OverlookedFactor] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)
    what_changed: str = Field(description="How the user's answers changed the analysis")
    safety_flag: bool = Field(default=False)
    guard_notes: List[str] = Field(default_factory=list)


class SummaryResponse(StripModel):
    """Response for generating thinking summary."""

    session_id: str
    decision: str
    details: Optional[str] = None
    reasons: str
    decision_type: Optional[DecisionType] = None
    reasoning_map: ReasoningMap
    overlooked_factors: List[OverlookedFactor]
    assumptions: List[Assumption]
    conflicts: List[Conflict]
    questions: List[Question]
    answers: List[dict]  # User's answers to questions
    thinking_summary: str = Field(description="Formatted thinking summary for user")
    created_at: datetime = Field(default_factory=datetime.utcnow)
