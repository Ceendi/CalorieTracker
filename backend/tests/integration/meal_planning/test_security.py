import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.users.api.routes import current_active_user
from src.meal_planning.api.dependencies import get_current_user
from src.users.domain.models import User

@pytest.fixture
def user_a():
    return User(id=uuid.uuid4(), email="user_a@example.com", is_active=True, is_superuser=False, hashed_password="pwd")

@pytest.fixture
def client_anonymous():
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c

def test_meal_plan_generation_requires_auth(client_anonymous):
    # Act
    payload = {"start_date": "2026-01-01", "days": 7}
    response = client_anonymous.post("/api/v1/meal-plans/generate", json=payload)
    # Assert
    assert response.status_code == 401

def test_meal_plan_progress_requires_auth(client_anonymous):
    # Act
    task_id = str(uuid.uuid4())
    response = client_anonymous.get(f"/api/v1/meal-plans/generate/{task_id}/progress")
    # Assert
    assert response.status_code == 401

def test_meal_plan_status_requires_auth(client_anonymous):
    # Act
    task_id = str(uuid.uuid4())
    response = client_anonymous.get(f"/api/v1/meal-plans/generate/{task_id}/status")
    # Assert
    assert response.status_code == 401
