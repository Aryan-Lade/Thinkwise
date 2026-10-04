"""
Unit tests for Pydantic schemas
"""

import pytest
from pydantic import ValidationError
from app.models.schemas import (
    AnalysisResponse,
    ReasoningMap,
    OverlookedFactor,
    Assumption,
    Conflict,
    Question,
    DecisionType
)


def test_reasoning_map_creation():
    """Test creating a ReasoningMap instance."""
    reasoning_map = ReasoningMap(
        stated_factors=["factor1", "factor2"],
        stated_reasons=["reason1", "reason2"],
        most_visible_factors=["visible1"],
        thin_or_missing_areas=["thin1"]
    )

    assert len(reasoning_map.stated_factors) == 2
    assert len(reasoning_map.stated_reasons) == 2
    assert len(reasoning_map.most_visible_factors) == 1
    assert len(reasoning_map.thin_or_missing_areas) == 1


def test_overlooked_factor_creation():
    """Test creating an OverlookedFactor instance."""
    factor = OverlookedFactor(
        text="Test overlooked factor",
        why_it_matters="This matters because..."
    )

    assert factor.text == "Test overlooked factor"
    assert factor.why_it_matters == "This matters because..."
    assert factor.id is not None  # Should be auto-generated


def test_assumption_creation():
    """Test creating an Assumption instance."""
    assumption = Assumption(
        text="Test assumption",
        how_to_test="Test it by..."
    )

    assert assumption.text == "Test assumption"
    assert assumption.how_to_test == "Test it by..."
    assert assumption.id is not None


def test_conflict_creation():
    """Test creating a Conflict instance."""
    conflict = Conflict(
        statement_a="Statement A",
        statement_b="Statement B",
        tension="They conflict because..."
    )

    assert conflict.statement_a == "Statement A"
    assert conflict.statement_b == "Statement B"
    assert conflict.tension == "They conflict because..."
    assert conflict.id is not None


def test_question_creation():
    """Test creating a Question instance."""
    question = Question(
        theme="assumptions",
        text="What is your assumption?"
    )

    assert question.theme == "assumptions"
    assert question.text == "What is your assumption?"
    assert question.id is not None


def test_decision_type_enum():
    """Test DecisionType enum values."""
    assert DecisionType.CAREER == "career"
    assert DecisionType.EDUCATION == "education"
    assert DecisionType.FINANCIAL == "financial"
    assert DecisionType.STARTUP == "startup"
    assert DecisionType.PERSONAL == "personal"
    assert DecisionType.RELATIONSHIP == "relationship"
    assert DecisionType.HEALTH == "health"
    assert DecisionType.PURCHASE == "purchase"
    assert DecisionType.OTHER == "other"


def test_analysis_response_creation():
    """Test creating an AnalysisResponse instance."""
    response_data = {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 1,
        "decision_restated": "Test decision",
        "reasoning_map": {
            "stated_factors": ["factor1"],
            "stated_reasons": ["reason1"],
            "most_visible_factors": ["visible1"],
            "thin_or_missing_areas": ["thin1"]
        },
        "overlooked_factors": [],
        "assumptions": [],
        "conflicts": [],
        "questions": [],
        "safety_flag": False,
        "guard_notes": []
    }

    response = AnalysisResponse(**response_data)

    assert response.session_id == "123e4567-e89b-12d3-a456-426614174000"
    assert response.round == 1
    assert response.decision_restated == "Test decision"
    assert response.safety_flag == False
    assert len(response.guard_notes) == 0


def test_analysis_response_validation():
    """Test validation of AnalysisResponse."""
    # Test missing required fields
    with pytest.raises(ValidationError):
        AnalysisResponse(
            session_id="test",
            round=1,
            decision_restated="Test"
            # Missing reasoning_map which is required
        )

    # Test invalid safety_flag type
    with pytest.raises(ValidationError):
        AnalysisResponse(
            session_id="test",
            round=1,
            decision_restated="Test",
            reasoning_map={
                "stated_factors": [],
                "stated_reasons": [],
                "most_visible_factors": [],
                "thin_or_missing_areas": []
            },
            overlooked_factors=[],
            assumptions=[],
            conflicts=[],
            questions=[],
            safety_flag="not_a_boolean",  # Should be boolean
            guard_notes=[]
        )


def test_empty_lists_are_allowed():
    """Test that empty lists are allowed for optional fields."""
    response_data = {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 1,
        "decision_restated": "Test decision",
        "reasoning_map": {
            "stated_factors": [],
            "stated_reasons": [],
            "most_visible_factors": [],
            "thin_or_missing_areas": []
        },
        "overlooked_factors": [],  # Empty list allowed
        "assumptions": [],         # Empty list allowed
        "conflicts": [],           # Empty list allowed
        "questions": [],           # Empty list allowed
        "safety_flag": False,
        "guard_notes": []          # Empty list allowed
    }

    response = AnalysisResponse(**response_data)
    assert len(response.overlooked_factors) == 0
    assert len(response.assumptions) == 0
    assert len(response.conflicts) == 0
    assert len(response.questions) == 0
    assert len(response.guard_notes) == 0


def test_string_field_stripping():
    """Test that string fields are stripped of whitespace."""
    response_data = {
        "session_id": "  123e4567-e89b-12d3-a456-426614174000  ",
        "round": 1,
        "decision_restated": "  Test decision  ",
        "reasoning_map": {
            "stated_factors": ["  factor1  ", "  factor2  "],
            "stated_reasons": ["  reason1  "],
            "most_visible_factors": ["  visible1  "],
            "thin_or_missing_areas": ["  thin1  "]
        },
        "overlooked_factors": [
            {
                "id": "  of1  ",
                "text": "  Test factor  ",
                "why_it_matters": "  Test explanation  "
            }
        ],
        "assumptions": [],
        "conflicts": [],
        "questions": [],
        "safety_flag": False,
        "guard_notes": []
    }

    response = AnalysisResponse(**response_data)

    # Check that strings are stripped
    assert response.session_id == "123e4567-e89b-12d3-a456-426614174000"
    assert response.decision_restated == "Test decision"
    assert response.reasoning_map.stated_factors[0] == "factor1"
    assert response.reasoning_map.stated_factors[1] == "factor2"
    assert response.reasoning_map.stated_reasons[0] == "reason1"
    assert response.reasoning_map.most_visible_factors[0] == "visible1"
    assert response.reasoning_map.thin_or_missing_areas[0] == "thin1"
    assert response.overlooked_factors[0].id == "of1"
    assert response.overlooked_factors[0].text == "Test factor"
    assert response.overlooked_factors[0].why_it_matters == "Test explanation"


if __name__ == "__main__":
    pytest.main([__file__])