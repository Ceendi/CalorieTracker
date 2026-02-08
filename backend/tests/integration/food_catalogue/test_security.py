import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.food_catalogue.api.dependencies import get_food_service

@pytest.fixture
def user_a():
    return User(id=uuid.uuid4(), email="user_a@example.com", is_active=True, is_superuser=False, hashed_password="pwd")

@pytest.fixture
def mock_food_service():
    return AsyncMock()

@pytest.fixture
def client_a(user_a, mock_food_service):
    app.dependency_overrides[current_active_user] = lambda: user_a
    app.dependency_overrides[get_food_service] = lambda: mock_food_service
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides = {}

@pytest.fixture
def client_anonymous():
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c

def test_authentication_required_for_custom_food(client_anonymous):
    # Act
    payload = {"name": "Test", "nutrition": {"kcal_per_100g": 100, "protein_per_100g": 10, "fat_per_100g": 1, "carbs_per_100g": 10}}
    response = client_anonymous.post("/api/v1/foods/custom", json=payload)
    # Assert
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_food_isolation_search(client_a, mock_food_service, user_a):
    # Arrange
    mock_food_service.search_food.return_value = []
    
    # Act
    response = client_a.get("/api/v1/foods/search?q=private")
    
    # Assert
    assert response.status_code == 200
    mock_food_service.search_food.assert_called_once()
    assert mock_food_service.search_food.call_args[1]['user_id'] == user_a.id
