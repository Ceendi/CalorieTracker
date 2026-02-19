import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date

from src.main import app
from src.tracking.api.dependencies import get_tracking_service
from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.tracking.application.services import TrackingService
from src.tracking.domain.entities import DailyLog, MealType

# --- Fixtures ---

@pytest.fixture
def mock_tracking_repo():
    repo = AsyncMock()
    repo.commit = AsyncMock()
    return repo

@pytest.fixture
def mock_food_repo():
    return AsyncMock()

@pytest.fixture
def real_service_with_mocks(mock_tracking_repo, mock_food_repo):
    """
    Returns the REAL TrackingService but with MOCKED repositories.
    This tests the integration between Service and Repo layers (interfaces)
    and ensuring the Router calls the Service correctly.
    """
    return TrackingService(tracking_repo=mock_tracking_repo, food_repo=mock_food_repo)

@pytest.fixture
def test_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed"
    )

@pytest.fixture
def client(real_service_with_mocks, test_user):
    # Patch AI services imported in main.py to prevent loading models
    with patch("src.main.get_audio_service") as mock_audio, \
         patch("src.main.get_vision_service") as mock_vision:
        
        mock_audio_service = AsyncMock()
        mock_audio_service.warmup = AsyncMock()
        mock_audio.return_value = mock_audio_service
        mock_vision.return_value = AsyncMock()
        
        # Override dependencies
        # Key difference: We inject the REAL service (logic) with MOCKED DB
        app.dependency_overrides[get_tracking_service] = lambda: real_service_with_mocks
        app.dependency_overrides[current_active_user] = lambda: test_user
        
        with TestClient(app) as c:
            yield c
        
        # Clean up overrides
        app.dependency_overrides = {}

# --- Tests ---

def test_flow_add_entry_full(client, mock_tracking_repo, mock_food_repo):
    """
    Verifies the flow: Router -> Service -> Repositories.
    Checks if Router correctly extracts data, Service processes it (e.g., matching product),
    and Repositories are called with expected domain objects.
    """
    # Arrange
    product_id = uuid4()
    user_id = client.app.dependency_overrides[current_active_user]().id
    log_date = date.today()
    
    # Mock Food Repo finding the product
    mock_food_repo.get_by_id.return_value = MagicMock(
        id=product_id,
        name="Test Food",
        nutrition=MagicMock(kcal_per_100g=100, protein_per_100g=10, fat_per_100g=5, carbs_per_100g=10)
    )
    
    # Mock Tracking Repo returning a log
    mock_log = DailyLog(id=uuid4(), user_id=user_id, date=log_date, entries=[])
    mock_tracking_repo.get_or_create_daily_log.return_value = mock_log
    mock_tracking_repo.get_daily_log.return_value = mock_log

    payload = {
        "product_id": str(product_id),
        "amount_grams": 150.0,
        "date": str(log_date),
        "meal_type": "lunch"
    }

    # Act
    response = client.post("/api/v1/tracking/entries", json=payload)

    # Assert
    assert response.status_code == 201
    
    # Verify Service logic executed by checking Repo calls
    mock_food_repo.get_by_id.assert_called_once_with(product_id)
    mock_tracking_repo.get_or_create_daily_log.assert_called_once_with(user_id, log_date)
    
    # Verify correct data conversion in Service before calling Add Entry
    mock_tracking_repo.add_entry.assert_called_once()
    entry_arg = mock_tracking_repo.add_entry.call_args[0][1]
    assert entry_arg.amount_grams == 150.0  # Service passes this through
    assert entry_arg.meal_type == MealType.LUNCH
    
    mock_tracking_repo.recalculate_totals.assert_called_once_with(mock_log.id)
    mock_tracking_repo.commit.assert_called_once()


def test_flow_add_entry_validation_error(client, mock_tracking_repo):
    """
    Verifies that Router validation blocks invalid requests before they reach the Service.
    """
    payload = {
        "product_id": "invalid-uuid", # Invalid type
        "amount_grams": 100.0,
        "date": str(date.today()),
        "meal_type": "lunch"
    }

    response = client.post("/api/v1/tracking/entries", json=payload)

    assert response.status_code == 422
    # Service/Repo should NOT be called
    mock_tracking_repo.get_or_create_daily_log.assert_not_called()
