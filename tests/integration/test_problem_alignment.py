"""
Problem-alignment tests using the internship example fixture
"""

import json
import pytest
from fastapi.testclient import TestClient
from app.main import app


def load_internship_fixture():
    """Load the internship example fixture."""
    with open("tests/fixtures/internship_example.json", "r") as f:
        return json.load(f)


def test_internship_example_structure():
    """Test that the fixture has the expected structure."""
    fixture = load_internship_fixture()

    # Check required top-level fields
    assert "decision" in fixture
    assert "details" in fixture
    assert "reasons" in fixture
    assert "decision_type" in fixture
    assert "expected_analysis" in fixture

    # Check expected analysis structure
    expected = fixture["expected_analysis"]
    assert "reasoning_map" in expected
    assert "overlooked_factors" in expected
    assert "assumptions" in expected
    assert "conflicts" in expected
    assert "questions" in expected
    assert "safety_flag" in expected


def test_internship_example_analysis(client):
    """Test that the internship example produces expected analysis structure."""
    fixture = load_internship_fixture()

    # Prepare request data
    request_data = {
        "decision": fixture["decision"],
        "details": fixture["details"],
        "reasons": fixture["reasons"],
        "decision_type": fixture["decision_type"],
    }

    # Make request to analyze endpoint
    response = client.post("/api/v1/analyze", json=request_data)

    # Should succeed
    assert response.status_code == 200
    analysis = response.json()

    # Check that we got a session ID
    assert "session_id" in analysis
    assert analysis["session_id"] is not None

    # Check reasoning map structure
    assert "reasoning_map" in analysis
    rm = analysis["reasoning_map"]
    assert "stated_factors" in rm
    assert "stated_reasons" in rm
    assert "most_visible_factors" in rm
    assert "thin_or_missing_areas" in rm

    # Check that we extracted the stated factors correctly
    # (Exact matching might be difficult due to AI variability, so we check for presence)
    stated_factors = rm["stated_factors"]
    assert isinstance(stated_factors, list)
    assert len(stated_factors) > 0

    stated_reasons = rm["stated_reasons"]
    assert isinstance(stated_reasons, list)
    assert len(stated_reasons) > 0

    # Check that we got overlooked factors
    assert "overlooked_factors" in analysis
    overlooked = analysis["overlooked_factors"]
    assert isinstance(overlooked, list)
    # The AI should identify some overlooked factors for this example
    # We won't check exact count as it may vary, but should have some
    assert len(overlooked) >= 1

    # Check that we got assumptions
    assert "assumptions" in analysis
    assumptions = analysis["assumptions"]
    assert isinstance(assumptions, list)
    assert len(assumptions) >= 1

    # Check that we got conflicts
    assert "conflicts" in analysis
    conflicts = analysis["conflicts"]
    assert isinstance(conflicts, list)
    assert len(conflicts) >= 1

    # Check that we got questions
    assert "questions" in analysis
    questions = analysis["questions"]
    assert isinstance(questions, list)
    assert len(questions) >= 3  # Should generate several questions

    # Check question structure
    for question in questions:
        assert "id" in question
        assert "theme" in question
        assert "text" in question
        assert isinstance(question["text"], str)
        assert len(question["text"]) > 0

    # Check that safety_flag is present and boolean
    assert "safety_flag" in analysis
    assert isinstance(analysis["safety_flag"], bool)

    # For this example, safety_flag should be False (no crisis indicators)
    assert analysis["safety_flag"] == False

    # Check that guard_notes is present
    assert "guard_notes" in analysis
    assert isinstance(analysis["guard_notes"], list)


def test_internship_example_no_directive_language(client):
    """Test that the response contains no directive language."""
    fixture = load_internship_fixture()

    # Prepare request data
    request_data = {
        "decision": fixture["decision"],
        "details": fixture["details"],
        "reasons": fixture["reasons"],
        "decision_type": fixture["decision_type"],
    }

    # Make request to analyze endpoint
    response = client.post("/api/v1/analyze", json=request_data)

    assert response.status_code == 200
    analysis = response.json()

    # Define directive phrases to check for (same as in guard service)
    directive_phrases = [
        "you should",
        "i recommend",
        "the best option is",
        "go with",
        "you must",
        "my advice is",
        "choose ",
        "pick ",
        "select ",
        "opt for",
        "decide to",
        "it is better to",
        "you ought to",
        "i suggest you",
        "consider choosing",
        "go ahead and",
        "definitely choose",
        "without doubt",
        "clearly you should",
        "the right choice is",
        "i think you should",
        "in my opinion",
        "based on my analysis",
        "as an ai advisor",
        "according to my evaluation",
        "it would be wise to",
        "the smarter choice",
        "the more beneficial option",
        "you would be better off",
    ]

    # Fields to check for directive language
    string_fields_to_check = [
        "decision_restated",
        "what_would_change_your_mind",
        "reversibility_note",
    ]

    # Check simple string fields
    for field in string_fields_to_check:
        value = analysis.get(field)
        if value and isinstance(value, str):
            value_lower = value.lower()
            for phrase in directive_phrases:
                assert (
                    phrase not in value_lower
                ), f"Directive phrase '{phrase}' found in {field}: '{value}'"

    # Check complex fields
    complex_checks = [
        ("overlooked_factors", ["text", "why_it_matters"]),
        ("assumptions", ["text", "how_to_test"]),
        ("conflicts", ["statement_a", "statement_b", "tension"]),
        ("questions", ["text"]),
        ("possible_biases", ["why_it_may_apply"]),
    ]

    for field_name, subfields in complex_checks:
        items = analysis.get(field_name, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for subfield in subfields:
                        value = item.get(subfield)
                        if value and isinstance(value, str):
                            value_lower = value.lower()
                            for phrase in directive_phrases:
                                assert (
                                    phrase not in value_lower
                                ), f"Directive phrase '{phrase}' found in {field_name}.{subfield}: '{value}'"


def test_internship_example_refine_flow(client):
    """Test the refine flow with the internship example."""
    fixture = load_internship_fixture()

    # Step 1: Initial analysis
    request_data = {
        "decision": fixture["decision"],
        "details": fixture["details"],
        "reasons": fixture["reasons"],
        "decision_type": fixture["decision_type"],
    }

    response = client.post("/api/v1/analyze", json=request_data)
    assert response.status_code == 200
    analysis = response.json()

    session_id = analysis["session_id"]
    assert session_id is not None

    # Step 2: Prepare some mock answers to the questions
    questions = analysis.get("questions", [])
    if len(questions) > 0:
        # Create answers for first few questions
        answers = []
        for i, question in enumerate(
            questions[: min(3, len(questions))]
        ):  # Answer up to 3 questions
            answers.append(
                {
                    "question_id": question["id"],
                    "answer": f"This is my answer to question {i+1} about {question['theme']}.",
                }
            )

        # Step 3: Call refine endpoint
        refine_data = {"session_id": session_id, "answers": answers}

        refine_response = client.post("/api/v1/refine", json=refine_data)

        # Should succeed
        assert refine_response.status_code == 200
        refinement = refine_response.json()

        # Check refine response structure
        assert "session_id" in refinement
        assert refinement["session_id"] == session_id
        assert "round" in refinement
        assert refinement["round"] == 2  # Should be round 2
        assert "decision_restated" in refinement
        assert "reasoning_map" in refinement
        assert "overlooked_factors" in refinement
        assert "assumptions" in refinement
        assert "questions" in refinement
        assert "what_changed" in refinement
        assert "safety_flag" in refinement
        assert "guard_notes" in refinement

        # Check that we got a meaningful what_changed field
        what_changed = refinement.get("what_changed")
        assert isinstance(what_changed, str)
        assert len(what_changed) > 0

        # Check that guard notes are present
        assert isinstance(refinement["guard_notes"], list)


def test_internship_example_summary_flow(client):
    """Test the summary flow with the internship example."""
    fixture = load_internship_fixture()

    # Step 1: Initial analysis
    request_data = {
        "decision": fixture["decision"],
        "details": fixture["details"],
        "reasons": fixture["reasons"],
        "decision_type": fixture["decision_type"],
    }

    response = client.post("/api/v1/analyze", json=request_data)
    assert response.status_code == 200
    analysis = response.json()

    session_id = analysis["session_id"]
    assert session_id is not None

    # Step 2: Call summary endpoint (without refinement)
    summary_data = {"session_id": session_id}

    summary_response = client.post("/api/v1/summary", json=summary_data)

    # Should succeed
    assert summary_response.status_code == 200
    summary = summary_response.json()

    # Check summary response structure
    assert "session_id" in summary
    assert summary["session_id"] == session_id
    assert "decision" in summary
    assert "details" in summary
    assert "reasons" in summary
    assert "reasoning_map" in summary
    assert "overlooked_factors" in summary
    assert "assumptions" in summary
    assert "conflicts" in summary
    assert "questions" in summary
    assert "answers" in summary
    assert "thinking_summary" in summary
    assert "created_at" in summary

    # Check types
    assert isinstance(summary["session_id"], str)
    assert isinstance(summary["decision"], str)
    assert isinstance(summary["details"], (str, type(None)))
    assert isinstance(summary["reasons"], str)
    assert isinstance(summary["reasoning_map"], dict)
    assert isinstance(summary["overlooked_factors"], list)
    assert isinstance(summary["assumptions"], list)
    assert isinstance(summary["conflicts"], list)
    assert isinstance(summary["questions"], list)
    assert isinstance(summary["answers"], list)
    assert isinstance(summary["thinking_summary"], str)
    assert len(summary["thinking_summary"]) > 0

    # Check that the thinking summary contains expected sections
    thinking_summary = summary["thinking_summary"]
    assert "# My Thinking Summary" in thinking_summary
    assert "## Your Decision" in thinking_summary
    assert "decision" in thinking_summary.lower()

    # Step 3: Test with refinement (if we have questions)
    questions = analysis.get("questions", [])
    if len(questions) > 0:
        # Prepare answers
        answers = []
        for question in questions[: min(2, len(questions))]:  # Answer up to 2 questions
            answers.append(
                {
                    "question_id": question["id"],
                    "answer": f"My refined answer about {question['theme']}.",
                }
            )

        # Call refine first
        refine_data = {"session_id": session_id, "answers": answers}

        refine_response = client.post("/api/v1/refine", json=refine_data)
        assert refine_response.status_code == 200

        # Then call summary
        summary_response = client.post("/api/v1/summary", json=summary_data)
        assert summary_response.status_code == 200
        summary_with_refinement = summary_response.json()

        # Should have the answers in the summary
        assert len(summary_with_refinement["answers"]) == len(answers)

        # Thinking summary should still be present and meaningful
        assert len(summary_with_refinement["thinking_summary"]) > 0


def test_internship_example_specific_blind_spots(client):
    """
    R1-R6: Test asserting that the internship example output specifically:
    1. Covers academics impact
    2. Covers learning / mentorship quality
    3. Covers long-term career prospects
    4. Questions the stated assumptions with verification tests
    5. Contains zero directive language and no recommendation field
    """
    fixture = load_internship_fixture()
    response = client.post(
        "/api/v1/analyze",
        json={
            "decision": fixture["decision"],
            "details": fixture["details"],
            "reasons": fixture["reasons"],
            "decision_type": fixture["decision_type"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    all_text = json.dumps(data).lower()

    # 1. Output covers academics impact
    assert any(
        term in all_text
        for term in ["academic", "college", "course", "schedule", "grades"]
    ), "Expected analysis to cover academic impact"

    # 2. Output covers learning / mentorship quality
    assert any(
        term in all_text
        for term in ["mentor", "mentorship", "learning quality", "guidance"]
    ), "Expected analysis to cover learning/mentorship quality"

    # 3. Output covers long-term career prospects
    assert any(
        term in all_text for term in ["career", "long-term", "prospects", "future"]
    ), "Expected analysis to cover long-term career prospects"

    # 4. Questions the stated assumptions
    assumptions = data.get("assumptions", [])
    assert len(assumptions) >= 1
    for a in assumptions:
        assert "how_to_test" in a
        assert len(a["how_to_test"]) > 5

    # 5. Schema guarantee: NO recommendation field
    assert "recommendation" not in data
    assert "recommendations" not in data
    assert "suggested_decision" not in data
    assert "advised_choice" not in data

    # 6. Anti-directive language enforcement
    banned_phrases = [
        "you should",
        "i recommend",
        "the best option is",
        "my advice is",
        "you must",
        "definitely choose",
        "clearly you should",
    ]
    for banned in banned_phrases:
        assert (
            banned not in all_text
        ), f"Found directive banned phrase '{banned}' in output"


if __name__ == "__main__":
    pytest.main([__file__])
