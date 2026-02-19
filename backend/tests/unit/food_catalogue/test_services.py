import pytest
import uuid
from unittest.mock import AsyncMock
from src.food_catalogue.application.services import FoodService
from src.food_catalogue.domain.entities import Food, Nutrition

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def mock_external():
    return AsyncMock()

@pytest.fixture
def service(mock_repo, mock_external):
    return FoodService(repo=mock_repo, external=mock_external)

@pytest.fixture
def sample_food():
    return Food(
        id=uuid.uuid4(),
        name="Test Food",
        nutrition=Nutrition(kcal_per_100g=100, protein_per_100g=10, fat_per_100g=5, carbs_per_100g=10),
        barcode="123456",
        category="Test",
        source="local"
    )

class TestFoodService:
    @pytest.mark.asyncio
    async def test_search_food_local_only(self, service, mock_repo, mock_external, sample_food):
        # Arrange
        mock_repo.search_by_name.return_value = [sample_food] * 20
        
        # Act
        results = await service.search_food("query", limit=20)

        # Assert
        assert len(results) == 20
        mock_repo.search_by_name.assert_called_once()
        mock_external.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_food_combined(self, service, mock_repo, mock_external, sample_food):
        # Arrange
        mock_repo.search_by_name.return_value = [sample_food]
        external_food = Food(
            id=None, # Needs persistence
            name="External Food",
            nutrition=sample_food.nutrition,
            barcode="789",
            source="openfoodfacts"
        )
        mock_external.search.return_value = [external_food]
        
        persisted_food = Food(
            id=uuid.uuid4(),
            name="External Food",
            nutrition=sample_food.nutrition,
            barcode="789",
            source="openfoodfacts"
        )
        mock_repo.get_by_barcode.return_value = None
        mock_repo.save_custom_food.return_value = persisted_food

        # Act
        results = await service.search_food("query", limit=20)

        # Assert
        assert len(results) == 2
        assert results[0] == sample_food
        assert results[1] == persisted_food
        mock_external.search.assert_called_once()
        mock_repo.save_custom_food.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_barcode_local_hit(self, service, mock_repo, sample_food):
        # Arrange
        mock_repo.get_by_barcode.return_value = sample_food

        # Act
        result = await service.get_by_barcode("123456")

        # Assert
        assert result == sample_food
        mock_repo.get_by_barcode.assert_called_once_with("123456")

    @pytest.mark.asyncio
    async def test_get_by_barcode_external_hit(self, service, mock_repo, mock_external, sample_food):
        # Arrange
        mock_repo.get_by_barcode.side_effect = [None, None] # Not in DB, then not in DB during persistence check
        mock_external.fetch_by_barcode.return_value = sample_food
        mock_repo.save_custom_food.return_value = sample_food

        # Act
        result = await service.get_by_barcode("123456")

        # Assert
        assert result == sample_food
        mock_external.fetch_by_barcode.assert_called_once_with("123456")
        mock_repo.save_custom_food.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_custom_food(self, service, mock_repo, sample_food):
        # Arrange
        owner_id = uuid.uuid4()
        mock_repo.save_custom_food.return_value = sample_food

        # Act
        result = await service.create_custom_food(sample_food, owner_id)

        # Assert
        assert result == sample_food
        mock_repo.save_custom_food.assert_called_once()
        # Verify owner_id was set in the passed object to repo
        call_args = mock_repo.save_custom_food.call_args[0][0]
        assert call_args.owner_id == owner_id

    @pytest.mark.asyncio
    async def test_get_basic_products(self, service, mock_repo, sample_food):
        # Arrange
        mock_repo.get_by_source.return_value = [sample_food]

        # Act
        results = await service.get_basic_products(category="Owoce", limit=50)
        assert results == [sample_food]

    @pytest.mark.asyncio
    async def test_search_food_external_error(self, service, mock_repo, mock_external, sample_food):
        # Arrange
        mock_repo.search_by_name.return_value = [sample_food]
        mock_external.search.side_effect = Exception("API Down")
        
        # Act
        results = await service.search_food("query", limit=20)

        # Assert
        assert len(results) == 1
        assert results[0] == sample_food
        mock_external.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_external_product_duplicate_barcode(self, service, mock_repo, sample_food):
        # Arrange
        existing_food = sample_food
        mock_repo.get_by_barcode.return_value = existing_food
        
        # Act
        result = await service._persist_external_product(sample_food)

        # Assert
        assert result == existing_food
        mock_repo.save_custom_food.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_external_product_error(self, service, mock_repo, sample_food):
        # Arrange
        mock_repo.get_by_barcode.side_effect = Exception("DB Error")
        
        # Act
        result = await service._persist_external_product(sample_food)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_barcode_not_found_anywhere(self, service, mock_repo, mock_external):
        # Arrange
        mock_repo.get_by_barcode.return_value = None
        mock_external.fetch_by_barcode.return_value = None
        
        # Act
        result = await service.get_by_barcode("nonexistent")

        # Assert
        assert result is None
