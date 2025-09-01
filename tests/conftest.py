import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.config import settings


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_setup():
    """Setup test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> Generator:
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_okta_user():
    """Mock Okta user data for testing."""
    return {
        "sub": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "preferred_username": "testuser",
        "groups": ["users"],
        "scopes": ["survey:analyze", "survey:read", "survey:delete"]
    }


@pytest.fixture
def sample_survey_data():
    """Sample survey data for testing."""
    return {
        "title": "Test Performance Survey",
        "description": "A test survey for development purposes",
        "questions": [
            {
                "question_text": "How would you rate your communication skills?",
                "question_type": "multiple_choice",
                "category": "Communication",
                "weight": 1.0,
                "options": [
                    {"value": "1", "label": "Poor", "weight": 0.0},
                    {"value": "2", "label": "Fair", "weight": 0.5},
                    {"value": "3", "label": "Good", "weight": 1.0},
                    {"value": "4", "label": "Excellent", "weight": 1.5}
                ],
                "order_index": 1
            },
            {
                "question_text": "How would you rate your problem-solving skills?",
                "question_type": "multiple_choice",
                "category": "Problem Solving",
                "weight": 1.0,
                "options": [
                    {"value": "1", "label": "Poor", "weight": 0.0},
                    {"value": "2", "label": "Fair", "weight": 0.5},
                    {"value": "3", "label": "Good", "weight": 1.0},
                    {"value": "4", "label": "Excellent", "weight": 1.5}
                ],
                "order_index": 2
            }
        ],
        "answers": [
            {
                "question_id": 1,
                "selected_answer": "3",
                "answer_weight": 1.0
            },
            {
                "question_id": 2,
                "selected_answer": "4",
                "answer_weight": 1.0
            }
        ]
    }
