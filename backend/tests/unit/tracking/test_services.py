import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date

from src.tracking.application.services import TrackingService
from src.tracking.domain.entities import MealType, DailyLog, MealEntry
from src.tracking.domain.exceptions import ProductNotFoundInTrackingError, MealEntryNotFoundError
from src.food_catalogue.domain.entities import Food, Nutrition

@pytest.fixture
def mock_tracking_repo():
    repo = AsyncMock()
    repo.commit = AsyncMock()
    return repo

@pytest.fixture
def mock_food_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_tracking_repo, mock_food_repo):
    return TrackingService(tracking_repo=mock_tracking_repo, food_repo=mock_food_repo)

@pytest.fixture
def sample_food():
    return Food(
        id=uuid4(),
        name="Test Food",
        nutrition=Nutrition(kcal_per_100g=100, protein_per_100g=10, fat_per_100g=5, carbs_per_100g=10),
        barcode=None,
        category="Test Category",
    )

@pytest.fixture
def sample_daily_log():
    return DailyLog(
        id=uuid4(),
        user_id=uuid4(),
        date=date.today(),
        entries=[]
    )

class TestTrackingServiceAddEntry:
    @pytest.mark.asyncio
    async def test_add_meal_entry_success(self, service, mock_tracking_repo, mock_food_repo, sample_food, sample_daily_log):
        # Arrange
        user_id = uuid4()
        log_date = date.today()
        product_id = sample_food.id
        
        mock_food_repo.get_by_id.return_value = sample_food
        mock_tracking_repo.get_or_create_daily_log.return_value = sample_daily_log
        mock_tracking_repo.get_daily_log.return_value = sample_daily_log # Returns updated log

        # Act
        result = await service.add_meal_entry(
            user_id=user_id,
            log_date=log_date,
            meal_type=MealType.BREAKFAST,
            product_id=product_id,
            amount_grams=150
        )

        # Assert
        mock_food_repo.get_by_id.assert_called_once_with(product_id)
        mock_tracking_repo.get_or_create_daily_log.assert_called_once_with(user_id, log_date)
        
        # Verify entry creation passed to repo
        mock_tracking_repo.add_entry.assert_called_once()
        call_args = mock_tracking_repo.add_entry.call_args
        assert call_args[0][0] == user_id
        entry_arg = call_args[0][1]
        assert isinstance(entry_arg, MealEntry)
        assert entry_arg.amount_grams == 150
        assert entry_arg.product_id == product_id
        
        mock_tracking_repo.recalculate_totals.assert_called_once_with(sample_daily_log.id)
        mock_tracking_repo.commit.assert_called_once()
        assert result == sample_daily_log

    @pytest.mark.asyncio
    async def test_add_meal_entry_product_not_found(self, service, mock_food_repo):
        mock_food_repo.get_by_id.return_value = None
        product_id = uuid4()

        with pytest.raises(ProductNotFoundInTrackingError):
            await service.add_meal_entry(
                user_id=uuid4(),
                log_date=date.today(),
                meal_type=MealType.LUNCH,
                product_id=product_id,
                amount_grams=100
            )

class TestTrackingServiceBulkAdd:
    @pytest.mark.asyncio
    async def test_add_meal_entries_bulk_success(self, service, mock_tracking_repo, mock_food_repo, sample_food, sample_daily_log):
        user_id = uuid4()
        log_date = date.today()
        items = [
            {"product_id": sample_food.id, "amount_grams": 100},
            {"product_id": sample_food.id, "amount_grams": 200}
        ]

        mock_food_repo.get_by_id.side_effect = [sample_food, sample_food] # Returned twice
        mock_tracking_repo.get_or_create_daily_log.return_value = sample_daily_log
        mock_tracking_repo.get_daily_log.return_value = sample_daily_log

        await service.add_meal_entries_bulk(
            user_id=user_id,
            log_date=log_date,
            meal_type=MealType.DINNER,
            items=items
        )

        mock_tracking_repo.add_entries_bulk.assert_called_once()
        # Check that list of entries was passed
        entries_arg = mock_tracking_repo.add_entries_bulk.call_args[0][1]
        assert len(entries_arg) == 2
        
        mock_tracking_repo.recalculate_totals.assert_called_once()
        mock_tracking_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_meal_entries_bulk_product_not_found(self, service, mock_food_repo, sample_food, sample_daily_log, mock_tracking_repo):
        mock_food_repo.get_by_id.side_effect = [sample_food, None] # Second one fails
        mock_tracking_repo.get_or_create_daily_log.return_value = sample_daily_log
        
        items = [
            {"product_id": sample_food.id, "amount_grams": 100},
            {"product_id": uuid4(), "amount_grams": 200}
        ]

        with pytest.raises(ProductNotFoundInTrackingError):
            await service.add_meal_entries_bulk(
                user_id=uuid4(),
                log_date=date.today(),
                meal_type=MealType.DINNER,
                items=items
            )


class TestTrackingServiceRemove:
    @pytest.mark.asyncio
    async def test_remove_entry_success(self, service, mock_tracking_repo):
        entry_id = uuid4()
        user_id = uuid4()
        daily_log_id = uuid4()
        
        mock_entry = MagicMock(daily_log_id=daily_log_id)
        mock_tracking_repo.get_entry.return_value = mock_entry
        mock_tracking_repo.delete_entry.return_value = True

        await service.remove_entry(user_id, entry_id)

        mock_tracking_repo.delete_entry.assert_called_once_with(entry_id, user_id)
        mock_tracking_repo.recalculate_totals.assert_called_once_with(daily_log_id)
        mock_tracking_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_entry_not_found(self, service, mock_tracking_repo):
        mock_tracking_repo.get_entry.return_value = None
        
        with pytest.raises(MealEntryNotFoundError):
            await service.remove_entry(uuid4(), uuid4())

class TestTrackingServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_entry_success(self, service, mock_tracking_repo):
        entry_id = uuid4()
        user_id = uuid4()
        daily_log_id = uuid4()
        
        mock_entry = MagicMock(daily_log_id=daily_log_id, amount_grams=100)
        mock_tracking_repo.get_entry.return_value = mock_entry

        await service.update_meal_entry(
            user_id=user_id,
            entry_id=entry_id,
            amount_grams=250
        )

        assert mock_entry.amount_grams == 250
        mock_tracking_repo.update_entry.assert_called_once_with(mock_entry)
        mock_tracking_repo.recalculate_totals.assert_called_once_with(daily_log_id)
        mock_tracking_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_entry_not_found(self, service, mock_tracking_repo):
        mock_tracking_repo.get_entry.return_value = None
        
        with pytest.raises(MealEntryNotFoundError):
            await service.update_meal_entry(uuid4(), uuid4(), amount_grams=200)
