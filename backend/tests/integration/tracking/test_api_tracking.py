import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import unittest.mock
from uuid import uuid4
from datetime import date

from src.main import app
from src.tracking.api.dependencies import get_tracking_service
from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.tracking.domain.entities import DailyLog, MealEntry, MealType
from src.tracking.domain.exceptions import ProductNotFoundInTrackingError

# --- Fixtures ---

@pytest.fixture
def mock_service():
    service = AsyncMock()
    return service

@pytest.fixture
def test_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed" # Mocked
    )

@pytest.fixture
def client(mock_service, test_user):
    # Patch AI services imported in main.py to prevent loading models
    with unittest.mock.patch("src.main.get_audio_service") as mock_audio, \
         unittest.mock.patch("src.main.get_vision_service") as mock_vision:
        
        mock_audio_service = AsyncMock()
        mock_audio_service.warmup = AsyncMock()
        mock_audio.return_value = mock_audio_service
        
        mock_vision.return_value = AsyncMock()
        
        # Override dependencies
        app.dependency_overrides[get_tracking_service] = lambda: mock_service
        app.dependency_overrides[current_active_user] = lambda: test_user
        
        with TestClient(app) as c:
            yield c
        
        # Clean up overrides
        app.dependency_overrides = {}

# --- Tests ---

def test_add_entry_success(client, mock_service):
    # Arrange
    product_id = str(uuid4())
    payload = {
        "product_id": product_id,
        "amount_grams": 100.0,
        "date": str(date.today()),
        "meal_type": "breakfast",
        "unit_label": "g",
        "unit_grams": 1.0,
        "unit_quantity": 100.0
    }
    
    mock_log = DailyLog(
        id=uuid4(),
        user_id=uuid4(),
        date=date.today(),
        entries=[]
    )
    mock_service.add_meal_entry.return_value = mock_log

    # Act
    response = client.post("/api/v1/tracking/entries", json=payload)

    # Assert
    assert response.status_code == 201
    mock_service.add_meal_entry.assert_called_once()
    args = mock_service.add_meal_entry.call_args[1]
    assert str(args['product_id']) == product_id
    assert args['amount_grams'] == 100.0
    assert args['meal_type'] == MealType.BREAKFAST


def test_add_entry_product_not_found(client, mock_service):
    mock_service.add_meal_entry.side_effect = ProductNotFoundInTrackingError("123")
    
    payload = {
        "product_id": str(uuid4()),
        "amount_grams": 100.0,
        "date": str(date.today()),
        "meal_type": "breakfast"
    }
    
    response = client.post("/api/v1/tracking/entries", json=payload)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Product with id 123 not found"


def test_bulk_add_success(client, mock_service):
    payload = {
        "date": str(date.today()),
        "meal_type": "lunch",
        "items": [
            {"product_id": str(uuid4()), "amount_grams": 50},
            {"product_id": str(uuid4()), "amount_grams": 100}
        ]
    }
    
    mock_log = DailyLog(
        id=uuid4(),
        user_id=uuid4(),
        date=date.today(),
        entries=[]
    )
    mock_service.add_meal_entries_bulk.return_value = mock_log
    
    response = client.post("/api/v1/tracking/bulk-entries", json=payload)
    
    assert response.status_code == 201
    mock_service.add_meal_entries_bulk.assert_called_once()
    
def test_get_daily_log_success(client, mock_service):
    log_date = date.today()
    mock_log = DailyLog(
        id=uuid4(),
        user_id=uuid4(),
        date=log_date,
        entries=[
            MealEntry(
                id=uuid4(), daily_log_id=uuid4(), meal_type=MealType.BREAKFAST,
                product_name="Egg", amount_grams=100,
                kcal_per_100g=150, protein_per_100g=12, fat_per_100g=10, carbs_per_100g=1
            )
        ]
    )
    mock_service.get_daily_log.return_value = mock_log
    
    response = client.get(f"/api/v1/tracking/daily/{log_date}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(log_date)
    assert len(data["entries"]) == 1
    assert data["total_kcal"] == 150

def test_get_daily_log_empty(client, mock_service):
    # Service returns None, endpoint should return empty log structure
    mock_service.get_daily_log.return_value = None
    log_date = date.today()
    
    response = client.get(f"/api/v1/tracking/daily/{log_date}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_kcal"] == 0
    assert data["entries"] == []

def test_delete_entry_success(client, mock_service):
    entry_id = str(uuid4())
    mock_service.remove_entry.return_value = None
    
    response = client.delete(f"/api/v1/tracking/entries/{entry_id}")
    
    assert response.status_code == 204
    mock_service.remove_entry.assert_called_once()

def test_update_entry_success(client, mock_service):
    entry_id = str(uuid4())
    payload = {"amount_grams": 200.0}
    mock_service.update_meal_entry.return_value = None
    
    response = client.patch(f"/api/v1/tracking/entries/{entry_id}", json=payload)
    
    assert response.status_code == 204
    mock_service.update_meal_entry.assert_called_once()
    assert mock_service.update_meal_entry.call_args[1]['amount_grams'] == 200.0
