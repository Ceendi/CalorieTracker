import pytest
from uuid import uuid4
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from src.tracking.infrastructure.repositories import SqlAlchemyTrackingRepository
from src.tracking.infrastructure.orm_models import TrackingDailyLog, TrackingMealEntry
from src.tracking.domain.entities import MealEntry, MealType

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    return session

@pytest.fixture
def repo(mock_session):
    return SqlAlchemyTrackingRepository(mock_session)

@pytest.fixture
def sample_orm_log():
    log_id = uuid4()
    user_id = uuid4()
    log_date = date.today()
    
    orm_log = TrackingDailyLog(
        id=log_id,
        user_id=user_id,
        date=log_date,
        total_kcal=0,
        total_protein=0.0,
        total_fat=0.0,
        total_carbs=0.0
    )
    orm_log.entries = []
    return orm_log

@pytest.fixture
def sample_orm_entry(sample_orm_log):
    return TrackingMealEntry(
        id=uuid4(),
        daily_log_id=sample_orm_log.id,
        product_id=uuid4(),
        product_name="Test Product",
        meal_type="breakfast",
        amount_grams=100.0,
        kcal_per_100g=200,
        protein_per_100g=10.0,
        fat_per_100g=5.0,
        carbs_per_100g=20.0
    )

class TestSqlAlchemyTrackingRepository:
    
    @pytest.mark.asyncio
    async def test_to_domain_mapping(self, repo, sample_orm_log, sample_orm_entry):
        # Arrange
        sample_orm_log.entries = [sample_orm_entry]
        
        # Act
        domain_log = repo._to_domain(sample_orm_log)
        
        # Assert
        assert domain_log.id == sample_orm_log.id
        assert domain_log.user_id == sample_orm_log.user_id
        assert len(domain_log.entries) == 1
        
        entry = domain_log.entries[0]
        assert entry.id == sample_orm_entry.id
        assert entry.product_name == "Test Product"
        assert entry.meal_type == MealType.BREAKFAST
        assert entry.kcal_per_100g == 200

    @pytest.mark.asyncio
    async def test_domain_to_orm_mapping(self, repo):
        # Arrange
        entry = MealEntry(
            id=uuid4(),
            daily_log_id=uuid4(),
            meal_type=MealType.LUNCH,
            product_id=uuid4(),
            product_name="Domain Food",
            amount_grams=150.0,
            kcal_per_100g=100,
            protein_per_100g=5.0,
            fat_per_100g=2.0,
            carbs_per_100g=10.0
        )
        
        # Act
        orm_entry = repo._domain_entry_to_orm(entry)
        
        # Assert
        assert orm_entry.id == entry.id
        assert orm_entry.product_name == "Domain Food"
        assert orm_entry.meal_type == "lunch"
        assert orm_entry.amount_grams == 150.0

    @pytest.mark.asyncio
    async def test_recalculate_totals_math(self, repo, mock_session, sample_orm_log):
        # Arrange
        # Entry 1: 150g of (200 kcal, 10p, 5f, 20c) -> 300 kcal, 15p, 7.5f, 30c
        e1 = TrackingMealEntry(
            amount_grams=150.0,
            kcal_per_100g=200,
            protein_per_100g=10.0,
            fat_per_100g=5.0,
            carbs_per_100g=20.0
        )
        # Entry 2: 50g of (100 kcal, 2p, 1f, 10c) -> 50 kcal, 1p, 0.5f, 5c
        e2 = TrackingMealEntry(
            amount_grams=50.0,
            kcal_per_100g=100,
            protein_per_100g=2.0,
            fat_per_100g=1.0,
            carbs_per_100g=10.0
        )
        sample_orm_log.entries = [e1, e2]
        
        # Mock session result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_log
        mock_session.execute.return_value = mock_result
        
        # Act
        await repo.recalculate_totals(sample_orm_log.id)
        
        # Assert
        # Totals: 300+50=350 kcal, 15+1=16p, 7.5+0.5=8f, 30+5=35c
        assert sample_orm_log.total_kcal == 350
        assert sample_orm_log.total_protein == 16.0
        assert sample_orm_log.total_fat == 8.0
        assert sample_orm_log.total_carbs == 35.0
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_entry(self, repo, mock_session):
        entry = MealEntry(
            id=uuid4(), daily_log_id=uuid4(), meal_type=MealType.BREAKFAST,
            product_id=uuid4(), product_name="X", amount_grams=100,
            kcal_per_100g=100, protein_per_100g=1, fat_per_100g=1, carbs_per_100g=1
        )
        
        await repo.add_entry(uuid4(), entry)
        
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_entries_bulk(self, repo, mock_session):
        entries = [
            MealEntry(id=uuid4(), daily_log_id=uuid4(), meal_type=MealType.BREAKFAST,
                     product_id=uuid4(), product_name="X", amount_grams=100,
                     kcal_per_100g=100, protein_per_100g=1, fat_per_100g=1, carbs_per_100g=1)
        ]
        
        await repo.add_entries_bulk(uuid4(), entries)
        
        mock_session.add_all.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_daily_log_found(self, repo, mock_session, sample_orm_log):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_log
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_daily_log(uuid4(), date.today())
        
        assert result is not None
        assert result.id == sample_orm_log.id

    @pytest.mark.asyncio
    async def test_get_daily_log_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_daily_log(uuid4(), date.today())
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_create_daily_log_existing(self, repo, mock_session, sample_orm_log):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_log
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_or_create_daily_log(uuid4(), date.today())
        
        assert result.id == sample_orm_log.id
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_daily_log_new(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None # Not found
        mock_session.execute.return_value = mock_result
        
        # After add, we usually refresh. Mock refresh to avoid error.
        mock_session.refresh = AsyncMock()

        result = await repo.get_or_create_daily_log(uuid4(), date.today())
        
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_entry_found(self, repo, mock_session, sample_orm_entry):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_entry
        mock_session.execute.return_value = mock_result
        
        result = await repo.delete_entry(uuid4(), uuid4())
        
        assert result is True
        mock_session.delete.assert_called_once_with(sample_orm_entry)

    @pytest.mark.asyncio
    async def test_delete_entry_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repo.delete_entry(uuid4(), uuid4())
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_entry_found(self, repo, mock_session, sample_orm_entry):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_entry
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_entry(uuid4(), uuid4())
        
        assert result is not None
        assert result.id == sample_orm_entry.id

    @pytest.mark.asyncio
    async def test_get_entry_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_entry(uuid4(), uuid4())
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_entry_found(self, repo, mock_session, sample_orm_entry):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_orm_entry
        mock_session.execute.return_value = mock_result
        
        entry_domain = MealEntry(
            id=sample_orm_entry.id, daily_log_id=uuid4(), meal_type=MealType.DINNER,
            product_id=uuid4(), product_name="X", amount_grams=500,
            kcal_per_100g=100, protein_per_100g=1, fat_per_100g=1, carbs_per_100g=1
        )
        
        await repo.update_entry(entry_domain)
        
        assert sample_orm_entry.amount_grams == 500
        assert sample_orm_entry.meal_type == "dinner"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history(self, repo, mock_session, sample_orm_log):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_orm_log]
        mock_session.execute.return_value = mock_result
        
        result = await repo.get_history(uuid4(), date.today(), date.today())
        
        assert len(result) == 1
        assert result[0].id == sample_orm_log.id

    @pytest.mark.asyncio
    async def test_commit(self, repo, mock_session):
        await repo.commit()
        mock_session.commit.assert_called_once()
