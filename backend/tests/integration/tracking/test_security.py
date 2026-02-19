import pytest
import uuid
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.tracking.api.dependencies import get_tracking_service
from src.tracking.domain.exceptions import MealEntryNotFoundError

@pytest.fixture
def user_a():
    return User(id=uuid.uuid4(), email="user_a@example.com", is_active=True, is_superuser=False, hashed_password="pwd")

@pytest.fixture
def mock_tracking_service():
    return AsyncMock()

@pytest.fixture
def client_a(user_a, mock_tracking_service):
    app.dependency_overrides[current_active_user] = lambda: user_a
    app.dependency_overrides[get_tracking_service] = lambda: mock_tracking_service
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c
    app.dependency_overrides = {}

@pytest.fixture
def client_anonymous():
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c

def test_authentication_required(client_anonymous):
    # Act
    response = client_anonymous.get("/api/v1/tracking/daily/2026-01-01")
    # Assert
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_idor_delete_other_user_entry(client_a, mock_tracking_service):
    # Arrange
    mock_tracking_service.remove_entry.side_effect = MealEntryNotFoundError("123")
    entry_id = str(uuid.uuid4())
    
    # Act
    response = client_a.delete(f"/api/v1/tracking/entries/{entry_id}")
    
    # Assert
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_idor_update_other_user_entry(client_a, mock_tracking_service):
    # Arrange
    mock_tracking_service.update_meal_entry.side_effect = MealEntryNotFoundError("123")
    entry_id = str(uuid.uuid4())
    
    # Act
    response = client_a.patch(f"/api/v1/tracking/entries/{entry_id}", json={"amount_grams": 500})
    
    # Assert
    assert response.status_code == 404

def test_inactive_user_blocked(user_a):
    # Arrange
    user_a.is_active = False
    
    async def mock_inactive_user_gatekeeper():
        raise HTTPException(status_code=401, detail="Inactive user")
        
    app.dependency_overrides[current_active_user] = mock_inactive_user_gatekeeper
    
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as client:
            # Act
            response = client.get("/api/v1/tracking/daily/2026-01-01")
            # Assert
            assert response.status_code == 401 
    app.dependency_overrides = {}
