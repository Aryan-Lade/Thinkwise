"""
Pytest configuration and offline fixtures for Blind Spot AI Thinking Companion.
Enforces 100% offline, deterministic testing with fully mocked Gemini API.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    AnalysisResponse,
    RefineResponse,
    ReasoningMap,
    OverlookedFactor,
    Assumption,
    Conflict,
    Question,
    Bias,
)
from app.services.gemini_service import gemini_service


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_decision_data():
    """Sample decision data for testing."""
    return {
        "decision": "Whether to accept a 6-month internship offer",
        "details": "Good stipend, close to home, working hours 9-5, role in software development, learning opportunities include industry tools, college schedule has classes Monday-Thursday",
        "reasons": "Mainly considering it because the stipend is good, the company is close to home, and it will provide industry experience",
        "decision_type": "career",
    }


def load_internship_fixture_data() -> Dict[str, Any]:
    """Helper to load the internship fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "internship_example.json"
    if fixture_path.exists():
        with open(fixture_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@pytest.fixture
def internship_expected_analysis() -> AnalysisResponse:
    """Fixture providing an AnalysisResponse constructed from internship_example.json."""
    data = load_internship_fixture_data()
    expected = data.get("expected_analysis", {})

    return AnalysisResponse(
        session_id="123e4567-e89b-12d3-a456-426614174000",
        round=1,
        decision_restated=data.get("decision", "Accept a 6-month internship offer"),
        reasoning_map=ReasoningMap(
            stated_factors=expected.get("reasoning_map", {}).get(
                "stated_factors",
                [
                    "good stipend",
                    "close to home",
                    "software development role",
                    "college schedule classes",
                ],
            ),
            stated_reasons=expected.get("reasoning_map", {}).get(
                "stated_reasons",
                [
                    "stipend is good",
                    "company is close to home",
                    "will provide industry experience",
                ],
            ),
            most_visible_factors=expected.get("reasoning_map", {}).get(
                "most_visible_factors",
                ["stipend is good", "company is close to home", "industry experience"],
            ),
            thin_or_missing_areas=expected.get("reasoning_map", {}).get(
                "thin_or_missing_areas",
                [
                    "impact on academics",
                    "actual learning quality",
                    "mentorship opportunities",
                    "long-term career fit",
                ],
            ),
        ),
        overlooked_factors=[
            OverlookedFactor(
                id=f"of{i+1}", text=item["text"], why_it_matters=item["why_it_matters"]
            )
            for i, item in enumerate(
                expected.get(
                    "overlooked_factors",
                    [
                        {
                            "text": "Impact on academic performance and college schedule balance",
                            "why_it_matters": "The internship during academic term could affect grades and course comprehension",
                        },
                        {
                            "text": "Quality and accessibility of mentorship in the role",
                            "why_it_matters": "Learning quality depends directly on mentorship and guidance available",
                        },
                        {
                            "text": "Long-term career alignment with personal goals",
                            "why_it_matters": "Day-to-day software development tasks may not match desired future career direction",
                        },
                    ],
                )
            )
        ],
        assumptions=[
            Assumption(id=f"a{i+1}", text=item["text"], how_to_test=item["how_to_test"])
            for i, item in enumerate(
                expected.get(
                    "assumptions",
                    [
                        {
                            "text": "Good stipend automatically means the opportunity is worthwhile",
                            "how_to_test": "Calculate actual hourly rate after taxes and travel expenses",
                        },
                        {
                            "text": "Close to home means minimal inconvenience",
                            "how_to_test": "Map commute during peak hours and consider energy drain",
                        },
                    ],
                )
            )
        ],
        conflicts=[
            Conflict(
                id=f"c{i+1}",
                statement_a=item["statement_a"],
                statement_b=item["statement_b"],
                tension=item["tension"],
            )
            for i, item in enumerate(
                expected.get(
                    "conflicts",
                    [
                        {
                            "statement_a": "I want valuable industry experience for my career",
                            "statement_b": "I am deciding primarily based on stipend and proximity rather than mentorship",
                            "tension": "Potential mismatch between stated career goals and actual decision drivers",
                        }
                    ],
                )
            )
        ],
        stakeholders=[],
        alternatives_not_considered=[],
        possible_biases=[
            Bias(
                name="Salience Bias",
                why_it_may_apply="Immediate visible perks like proximity and stipend overshadow less visible factors like mentorship quality.",
            )
        ],
        questions=[
            Question(id=f"q{i+1}", theme=item["theme"], text=item["text"])
            for i, item in enumerate(
                expected.get(
                    "questions",
                    [
                        {
                            "theme": "assumptions",
                            "text": "What specific evidence would convince you that the stipend truly represents good value for your time?",
                        },
                        {
                            "theme": "overlooked_factors",
                            "text": "How would you evaluate the actual quality of mentorship and learning opportunities available in this role?",
                        },
                        {
                            "theme": "tradeoffs",
                            "text": "How will you protect your college academic performance while working 9-5?",
                        },
                    ],
                )
            )
        ],
        what_would_change_your_mind=None,
        reversibility_note="A 6-month internship is relatively reversible, though semester credits lost cannot be easily recouped.",
        safety_flag=False,
        guard_notes=[],
    )


@pytest.fixture(autouse=True)
def mock_gemini_offline(monkeypatch, internship_expected_analysis):
    """
    Autouse fixture that ensures Gemini API calls are mocked 100% offline.
    Never hits Google GenAI network servers during standard tests.
    """

    async def mock_analyze_decision(
        decision: str,
        details: Optional[str] = None,
        reasons: str = "",
        decision_type: Optional[str] = None,
    ) -> AnalysisResponse:
        resp = internship_expected_analysis.model_copy(deep=True)
        resp.decision_restated = f"Whether to proceed with: {decision}"
        return resp

    async def mock_refine_analysis(
        session_id: str,
        answers: List[Dict[str, str]],
        previous_analysis: Optional[AnalysisResponse] = None,
    ) -> RefineResponse:
        return RefineResponse(
            session_id=session_id,
            round=2,
            decision_restated="Whether to accept a 6-month internship offer (Refined)",
            reasoning_map=internship_expected_analysis.reasoning_map,
            overlooked_factors=internship_expected_analysis.overlooked_factors,
            assumptions=internship_expected_analysis.assumptions,
            questions=[
                Question(
                    id="q_ref_1",
                    theme="reflection",
                    text="How might this choice look in 12 months in retrospect?",
                )
            ],
            what_changed="Clarified mentorship expectations and scheduled structured weekly check-ins.",
            safety_flag=False,
            guard_notes=[],
        )

    monkeypatch.setattr(gemini_service, "analyze_decision", mock_analyze_decision)
    monkeypatch.setattr(gemini_service, "refine_analysis", mock_refine_analysis)
