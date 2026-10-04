"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app


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
        "decision_type": "career"
    }


@pytest.fixture
def sample_analysis_response():
    """Sample analysis response for testing."""
    return {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 1,
        "decision_restated": "Whether to accept a 6-month software development internship with a good stipend, located close to home, with 9-5 working hours",
        "reasoning_map": {
            "stated_factors": ["good stipend", "close to home", "software development role", "industry tools learning", "9-5 working hours", "college schedule Monday-Thursday"],
            "stated_reasons": ["stipend is good", "company is close to home", "will provide industry experience"],
            "most_visible_factors": ["stipend is good", "company is close to home", "industry experience"],
            "thin_or_missing_areas": ["impact on academics", "actual learning quality", "mentorship opportunities", "long-term career fit", "workload balance", "opportunity cost"]
        },
        "overlooked_factors": [
            {
                "id": "of1",
                "text": "Impact on academic performance and college schedule balance",
                "why_it_matters": "The internship during academic term could affect grades, course comprehension, and ability to participate in campus activities"
            },
            {
                "id": "of2",
                "text": "Quality and accessibility of mentorship in the role",
                "why_it_matters": "Industry experience varies greatly depending on mentorship quality - poor mentorship could limit learning despite the prestigious company name"
            }
        ],
        "assumptions": [
            {
                "id": "a1",
                "text": "Good stipend automatically means the opportunity is worthwhile",
                "how_to_test": "Calculate actual hourly rate after taxes and compare to other opportunities; consider what the stipend doesn't cover (transportation, meals, etc.)"
            },
            {
                "id": "a2",
                "text": "Close to home means low cost and minimal inconvenience",
                "how_to_test": "Map out actual commute time and costs; consider time value of that commute versus other uses"
            }
        ],
        "conflicts": [
            {
                "id": "c1",
                "statement_a": "I want to gain valuable industry experience for my career",
                "statement_b": "I'm choosing based primarily on stipend and proximity rather than learning opportunities",
                "tension": "There's a potential mismatch between stated career goals and actual decision drivers"
            }
        ],
        "questions": [
            {
                "id": "q1",
                "theme": "assumptions",
                "text": "What specific evidence would convince you that the stipend truly represents good value for your time?"
            },
            {
                "id": "q2",
                "theme": "overlooked_factors",
                "text": "How would you evaluate the actual quality of mentorship and learning opportunities available in this role?"
            }
        ],
        "safety_flag": False,
        "guard_notes": []
    }


@pytest.fixture
def sample_refinement_response():
    """Sample refinement response for testing."""
    return {
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "round": 2,
        "decision_restated": "Whether to accept a 6-month software development internship with a good stipend, located close to home, with 9-5 working hours",
        "reasoning_map": {
            "stated_factors": ["good stipard", "close to home", "software development role", "industry tools learning", "9-5 working hours", "college schedule Monday-Thursday"],
            "stated_reasons": ["stipend is good", "company is close to home", "will provide industry experience"],
            "most_visible_factors": ["stipend is good", "company is close to home", "industry experience"],
            "thin_or_missing_areas": ["impact on academics", "actual learning quality", "mentorship opportunities", "long-term career fit", "workload balance", "opportunity cost"]
        },
        "overlooked_factors": [
            {
                "id": "of1",
                "text": "Impact on academic performance and college schedule balance",
                "why_it_matters": "The internship during academic term could affect grades, course comprehension, and ability to participate in campus activities"
            }
        ],
        "assumptions": [
            {
                "id": "a1",
                "text": "Good stipend automatically means the opportunity is worthwhile",
                "how_to_test": "Calculate actual hourly rate after taxes and compare to other opportunities; consider what the stipend doesn't cover (transportation, meals, etc.)"
            }
        ],
        "questions": [
            {
                "id": "q3",
                "theme": "time_horizon",
                "text": "How might your feelings about this decision change in 6 months, 1 year, or 5 years from now?"
            }
        ],
        "what_changed": "After reflecting on the mentorship quality, I realize I need to investigate the actual day-to-day work and supervision structure more thoroughly.",
        "safety_flag": False,
        "guard_notes": []
    }