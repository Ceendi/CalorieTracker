import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.food_catalogue.infrastructure.repositories import SqlAlchemyFoodRepository
from src.food_catalogue.infrastructure.orm_models import FoodModel, FoodUnitModel
from src.food_catalogue.domain.entities import Food, Nutrition, UnitInfo

@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_session):
    return SqlAlchemyFoodRepository(mock_session)

@pytest.fixture
def sample_food_model():
    food_id = uuid.uuid4()
    return FoodModel(
        id=food_id,
        name="Jabłko",
        barcode="123456789",
        calories=52.0,
        protein=0.3,
        fat=0.2,
        carbs=14.0,
        category="Owoce",
        default_unit="g",
        source="fineli",
        units=[
            FoodUnitModel(unit="sztuka", grams=150.0, label="1 sztuka (150g)")
        ]
    )

class TestSqlAlchemyFoodRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session, sample_food_model):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_food_model
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id(sample_food_model.id)

        # Assert
        assert result is not None
        assert result.id == sample_food_model.id
        assert result.name == "Jabłko"
        assert result.nutrition.kcal_per_100g == 52.0
        assert len(result.units) == 1
        assert result.units[0].unit == "sztuka"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_id(uuid.uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_barcode_success(self, repository, mock_session, sample_food_model):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_food_model
        mock_session.execute.return_value = mock_result

        # Act
        result = await repository.get_by_barcode("123456789")

        # Assert
        assert result is not None
        assert result.barcode == "123456789"

    @pytest.mark.asyncio
    async def test_search_by_name_fuzzy(self, repository, mock_session, sample_food_model):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_food_model]
        mock_session.execute.return_value = mock_result

        # Act
        results = await repository.search_by_name("jablko")

        # Assert
        assert len(results) == 1
        assert results[0].name == "Jabłko"
        # Verify that regexp operator was used in the query
        args, kwargs = mock_session.execute.call_args
        stmt = args[0]
        assert "Jabłko" not in str(stmt) # Should be regex pattern [jJ][aA][bB][lLłŁ][kK][oOóÓ]
        assert "~*" in str(stmt)

    @pytest.mark.asyncio
    async def test_save_custom_food(self, repository, mock_session):
        # Arrange
        owner_id = uuid.uuid4()
        nutrition = Nutrition(kcal_per_100g=100, protein_per_100g=10, fat_per_100g=5, carbs_per_100g=10)
        food = Food(
            id=None,
            name="Custom Food",
            barcode="999",
            nutrition=nutrition,
            category="Custom",
            default_unit="g",
            owner_id=owner_id,
            source="user"
        )
        
        # We need to mock the refresh to set an ID for the model
        food_id = uuid.uuid4()
        def mock_refresh(model):
            model.id = food_id
            return None
        
        mock_session.refresh.side_effect = mock_refresh
        
        # Act
        result = await repository.save_custom_food(food)

        # Assert
        assert result.name == "Custom Food"
        assert result.id == food_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_source_with_category(self, repository, mock_session, sample_food_model):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_food_model]
        mock_session.execute.return_value = mock_result

        # Act
        results = await repository.get_by_source(source="fineli", category="Owoce")

        # Assert
        assert len(results) == 1
        assert results[0].category == "Owoce"
        args, kwargs = mock_session.execute.call_args
        stmt = args[0]
        # Statement should have clauses
        compiled = stmt.compile()
        assert compiled.params['source_1'] == 'fineli'
        assert compiled.params['category_1'] == 'Owoce'
