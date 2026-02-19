import pytest
import uuid
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.food_catalogue.api.dependencies import get_food_service
from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.food_catalogue.domain.entities import Food, Nutrition

@pytest.fixture
def mock_food_service():
    return AsyncMock()

@pytest.fixture
def test_user():
    return User(
        id=uuid.uuid4(),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed"
    )

@pytest.fixture
def client(mock_food_service, test_user):
    # Patch AI services and dependencies
    with patch("src.main.get_audio_service"), \
         patch("src.main.get_vision_service"):
        
        app.dependency_overrides[get_food_service] = lambda: mock_food_service
        app.dependency_overrides[current_active_user] = lambda: test_user
        
        with TestClient(app) as c:
            yield c
        
        app.dependency_overrides = {}

@pytest.fixture
def sample_food():
    return Food(
        id=uuid.uuid4(),
        name="Jabłko",
        nutrition=Nutrition(kcal_per_100g=52, protein_per_100g=0.3, fat_per_100g=0.2, carbs_per_100g=14),
        barcode="123456",
        category="Owoce",
        source="fineli"
    )

class TestFoodCatalogueApi:
    def test_get_categories(self, client):
        response = client.get("/api/v1/foods/categories")
        assert response.status_code == 200
        assert "Owoce" in response.json()
        assert "Nabiał" in response.json()

    def test_search_food(self, client, mock_food_service, sample_food):
        # Arrange
        mock_food_service.search_food.return_value = [sample_food]
        
        # Act
        response = client.get("/api/v1/foods/search?q=jablko")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Jabłko"
        mock_food_service.search_food.assert_called_once()

    def test_get_product_by_id_success(self, client, mock_food_service, sample_food):
        # Arrange
        food_id = str(sample_food.id)
        mock_food_service.get_by_id.return_value = sample_food
        
        # Act
        response = client.get(f"/api/v1/foods/{food_id}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "Jabłko"
        mock_food_service.get_by_id.assert_called_once_with(food_id)

    def test_get_product_by_id_not_found(self, client, mock_food_service):
        # Arrange
        mock_food_service.get_by_id.return_value = None
        
        # Act
        response = client.get(f"/api/v1/foods/{uuid.uuid4()}")
        
        # Assert
        assert response.status_code == 404

    def test_get_product_by_barcode_success(self, client, mock_food_service, sample_food):
        # Arrange
        mock_food_service.get_by_barcode.return_value = sample_food
        
        # Act
        response = client.get("/api/v1/foods/barcode/123456")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["barcode"] == "123456"

    def test_create_custom_product_success(self, client, mock_food_service, sample_food):
        # Arrange
        mock_food_service.create_custom_food.return_value = sample_food
        payload = {
            "name": "Custom",
            "barcode": "999",
            "nutrition": {
                "kcal_per_100g": 100,
                "protein_per_100g": 10,
                "fat_per_100g": 1,
                "carbs_per_100g": 10
            }
        }
        
        # Act
        response = client.post("/api/v1/foods/custom", json=payload)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == "Jabłko" # Returned from mock
        mock_food_service.create_custom_food.assert_called_once()

    def test_get_basic_products(self, client, mock_food_service, sample_food):
        # Arrange
        mock_food_service.get_basic_products.return_value = [sample_food]
        
        # Act
        response = client.get("/api/v1/foods/basic?category=Owoce&limit=10")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        mock_food_service.get_basic_products.assert_called_once_with(category="Owoce", limit=10)
