import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from src.food_catalogue.infrastructure.adapters.openfoodfacts_adapter import OpenFoodFactsAdapter
from src.food_catalogue.domain.entities import Food, Nutrition

@pytest.fixture
def adapter():
    return OpenFoodFactsAdapter()

class TestOpenFoodFactsAdapter:
    def test_safe_float(self, adapter):
        assert adapter._safe_float(10.5) == 10.5
        assert adapter._safe_float("10,5") == 10.5
        assert adapter._safe_float("abc 123.4 def") == 123.4
        assert adapter._safe_float(None) == 0.0
        assert adapter._safe_float("invalid") == 0.0

    def test_extract_nutrition(self, adapter):
        data = {
            "nutriments": {
                "energy-kcal_100g": 100,
                "proteins_100g": 10,
                "fat_100g": 5,
                "carbohydrates_100g": 20
            }
        }
        nutrition = adapter._extract_nutrition(data)
        assert nutrition.kcal_per_100g == 100.0
        assert nutrition.protein_per_100g == 10.0
        assert nutrition.fat_per_100g == 5.0
        assert nutrition.carbs_per_100g == 20.0

    def test_extract_nutrition_fallback_kj(self, adapter):
        data = {
            "nutriments": {
                "energy-kcal_100g": 0,
                "energy_100g": 418.4, # 100 kcal
            }
        }
        nutrition = adapter._extract_nutrition(data)
        assert nutrition.kcal_per_100g == 100.0

    @pytest.mark.asyncio
    async def test_fetch_by_barcode_success(self, adapter):
        barcode = "123456789"
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "nutriments": {"energy-kcal_100g": 50}
            }
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await adapter.fetch_by_barcode(barcode)
            
        assert result is not None
        assert result.name == "Test Product"
        assert result.barcode == barcode

    @pytest.mark.asyncio
    async def test_fetch_by_barcode_not_found(self, adapter):
        barcode = "404"
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await adapter.fetch_by_barcode(barcode)
            
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_by_barcode_logical_failure(self, adapter):
        barcode = "000"
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 0}
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await adapter.fetch_by_barcode(barcode)
            
        assert result is None

    @pytest.mark.asyncio
    async def test_search_success(self, adapter):
        query = "apple"
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {
                    "code": "111",
                    "product_name": "Apple 1",
                    "nutriments": {"energy-kcal_100g": 50}
                },
                {
                    "code": "222",
                    "product_name": "Apple 2",
                    "nutriments": {"energy-kcal_100g": 60}
                }
            ]
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await adapter.search(query)
            
        assert len(results) == 2
        assert results[0].barcode == "111"
        assert results[1].barcode == "222"

    @pytest.mark.asyncio
    async def test_search_http_error(self, adapter):
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await adapter.search("query")
            
        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_by_barcode_exception(self, adapter):
        barcode = "123"
        with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection failed")):
            result = await adapter.fetch_by_barcode(barcode)
            
        assert result is None
