"""
Unit tests for the guard service
"""

import pytest
from app.services.guard_service import GuardService
from app.models.schemas import AnalysisResponse, RefineResponse


def test_guard_service_initialization():
    """Test that GuardService initializes correctly."""
    guard = GuardService()
    assert guard is not None
    assert hasattr(guard, 'directive_phrases')
    assert len(guard.directive_phrases) > 0


def test_check_for_directives_positive():
    """Test detection of directive language."""
    guard = GuardService()

    # Test various directive phrases
    test_cases = [
        "You should take this job.",
        "I recommend going with option A.",
        "The best option is to decline the offer.",
        "You must consider the long-term implications.",
        "My advice is to negotiate for better terms.",
        "Choose the internship because it pays well.",
        "Pick option B for better results.",
        "Select the first choice.",
        "Opt for the safer alternative.",
        "Decide to take the risk."
    ]

    for text in test_cases:
        has_directives, matches = guard.check_for_directives(text)
        assert has_directives == True, f"Failed to detect directive in: {text}"
        assert len(matches) > 0, f"No matches found for: {text}"


def test_check_for_directives_negative():
    """Test that non-directive text passes through."""
    guard = GuardService()

    # Test non-directive, question-based text
    test_cases = [
        "What are the potential benefits of this option?",
        "How might this decision affect your future goals?",
        "Which aspects of the role are most important to your development?",
        "What evidence would change your perspective on this matter?",
        "Consider the trade-offs between different factors involved.",
        "Reflect on how this aligns with your long-term objectives.",
        "Explore the possible consequences of each alternative.",
        "Examine whether the stated reasons hold up under scrutiny.",
        "Question whether the assumed benefits are guaranteed.",
        "Investigate the actual conditions and requirements involved."
    ]

    for text in test_cases:
        has_directives, matches = guard.check_for_directives(text)
        assert has_directives == False, f"Incorrectly flagged as directive: {text}"
        assert len(matches) == 0, f"Unexpected matches found: {matches}"


def test_check_for_directives_case_insensitive():
    """Test that directive detection is case insensitive."""
    guard = GuardService()

    test_cases = [
        "YOU SHOULD consider this.",
        "i recommend that option.",
        "The BEST OPTION is to proceed.",
        "You Must think about consequences.",
        "mY aDvIsE is to wait.",
        "cHoOsE the cheaper alternative."
    ]

    for text in test_cases:
        has_directives, matches = guard.check_for_directives(text)
        assert has_directives == True, f"Failed to detect directive (case insensitive): {text}"
        assert len(matches) > 0, f"No matches found for: {text}"


def test_sanitize_text():
    """Test sanitization of directive language."""
    guard = GuardService()

    original = "You should take the job because it pays well and I recommend it."
    sanitized = guard.sanitize_text(original, ["you should", "i recommend"])

    assert "you should" not in sanitized.lower()
    assert "i recommend" not in sanitized.lower()
    assert "[guidance removed]" in sanitized
    assert "because it pays well and" in sanitized


def test_validate_and_guard_analysis():
    """Test guarding an analysis response."""
    guard = GuardService()

    # Create an analysis with directive language
    analysis_data = {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 1,
        "decision_restated": "You should take this job",  # Directive!
        "reasoning_map": {
            "stated_factors": ["good pay"],
            "stated_reasons": ["I recommend this option"],  # Directive!
            "most_visible_factors": ["good pay"],
            "thin_or_missing_areas": []
        },
        "overlooked_factors": [
            {
                "id": "of1",
                "text": "You must consider work-life balance",  # Directive!
                "why_it_matters": "This is important for your health"
            }
        ],
        "assumptions": [],
        "conflicts": [],
        "questions": [
            {
                "id": "q1",
                "theme": "assumptions",
                "text": "Select the best option for your career"  # Directive!
            }
        ],
        "safety_flag": False,
        "guard_notes": []
    }

    analysis = AnalysisResponse(**analysis_data)
    guarded_analysis = guard.validate_and_guard_analysis(analysis)

    # Check that directive language has been sanitized
    assert "[guidance removed]" in guarded_analysis.decision_restated
    assert "[guidance removed]" in guarded_analysis.reasoning_map.stated_reasons[0]
    assert "[guidance removed]" in guarded_analysis.overlooked_factors[0].text
    assert "[guidance removed]" in guarded_analysis.questions[0].text

    # Check that guard notes were added
    assert len(guarded_analysis.guard_notes) > 0
    assert any("Directive language found" in note for note in guarded_analysis.guard_notes)


def test_validate_and_guard_analysis_clean():
    """Test that clean analysis passes through unchanged."""
    guard = GuardService()

    # Create a clean analysis with no directive language
    analysis_data = {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 1,
        "decision_restated": "Whether to accept the job offer",
        "reasoning_map": {
            "stated_factors": ["good pay", "location", "growth opportunities"],
            "stated_reasons": ["The compensation is competitive", "The location is convenient"],
            "most_visible_factors": ["good pay", "location"],
            "thin_or_missing_areas": ["work-life balance", "long-term prospects"]
        },
        "overlooked_factors": [
            {
                "id": "of1",
                "text": "Impact on professional development trajectory",
                "why_it_matters": "This role may affect future career opportunities"
            }
        ],
        "assumptions": [
            {
                "id": "a1",
                "text": "The stated compensation accurately reflects total value",
                "how_to_test": "Compare total compensation package including benefits and growth potential"
            }
        ],
        "conflicts": [
            {
                "id": "c1",
                "statement_a": "I want to maximize my earning potential",
                "statement_b": "I'm prioritizing work-life balance in my decision",
                "tension": "These goals may require different types of roles or industries"
            }
        ],
        "questions": [
            {
                "id": "q1",
                "theme": "assumptions",
                "text": "What factors contribute to the total compensation package beyond base salary?"
            }
        ],
        "safety_flag": False,
        "guard_notes": []
    }

    analysis = AnalysisResponse(**analysis_data)
    guarded_analysis = guard.validate_and_guard_analysis(analysis)

    # Should be essentially unchanged (except maybe for guard_notes being empty list)
    assert guarded_analysis.decision_restated == analysis.decision_restated
    assert guarded_analysis.reasoning_map.stated_reasons == analysis.reasoning_map.stated_reasons
    assert len(guarded_analysis.guard_notes) == 0  # No directives found


def test_validate_and_guard_refine():
    """Test guarding a refine response."""
    guard = GuardService()

    # Create a refine response with directive language
    refine_data = {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 2,
        "decision_restated": "You should reconsider your options",  # Directive!
        "reasoning_map": {
            "stated_factors": ["factor1"],
            "stated_reasons": ["reason1"],
            "most_visible_factors": ["visible1"],
            "thin_or_missing_areas": ["thin1"]
        },
        "overlooked_factors": [],
        "assumptions": [],
        "conflicts": [],
        "questions": [
            {
                "id": "q1",
                "theme": "assumptions",
                "text": "Choose the path that leads to success"  # Directive!
            }
        ],
        "what_changed": "I realized I must consider alternative perspectives",  # Directive!
        "safety_flag": False,
        "guard_notes": []
    }

    refine = RefineResponse(**refine_data)
    guarded_refine = guard.validate_and_guard_refine(refine)

    # Check that directive language has been sanitized
    assert "[guidance removed]" in guarded_refine.decision_restated
    assert "[guidance removed]" in guarded_refine.questions[0].text
    assert "[guidance removed]" in guarded_refine.what_changed

    # Check that guard notes were added
    assert len(guarded_refine.guard_notes) > 0


if __name__ == "__main__":
    pytest.main([__file__])