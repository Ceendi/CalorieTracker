"""
Unit tests for MealPlanService._enrich_meal_ingredients.

Tests that ingredients without food_id are properly enriched via
secondary search, nutrition is recalculated correctly, and meal
totals are updated after enrichment.
"""
import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from tests.unit.meal_planning.conftest import make_ingredient, make_meal, make_product


def _make_service(food_search=None, session=None):
    return MealPlanService(
        repository=MagicMock(),
        food_search=food_search,
        session=session,
    )


class TestEnrichMealIngredients:
    """Tests for _enrich_meal_ingredients."""

    @pytest.mark.asyncio
    async def test_skips_ingredients_with_food_id(self):
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock()
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Kurczak", food_id=uuid4())
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        mock_search.find_product_by_name.assert_not_called()
        assert result is meal  # Same object returned

    @pytest.mark.asyncio
    async def test_searches_for_ingredients_without_food_id(self):
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=None)
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Kurczak", auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        await service._enrich_meal_ingredients(meal)

        mock_search.find_product_by_name.assert_called_once()
        call_kwargs = mock_search.find_product_by_name.call_args
        assert call_kwargs.kwargs["name"] == "Kurczak"

    @pytest.mark.asyncio
    async def test_enriches_with_db_product(self):
        product = {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "name": "Kurczak piersi",
            "kcal_per_100g": 165,
            "protein_per_100g": 31.0,
            "fat_per_100g": 3.6,
            "carbs_per_100g": 0.0,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Kurczak", amount_grams=200.0, auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        enriched = result.ingredients[0]
        assert enriched.food_id == UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        assert enriched.name == "Kurczak piersi"

    @pytest.mark.asyncio
    async def test_recalculates_nutrition_from_db_values(self):
        product = {
            "id": str(uuid4()),
            "name": "Ryz",
            "kcal_per_100g": 130,
            "protein_per_100g": 2.7,
            "fat_per_100g": 0.3,
            "carbs_per_100g": 28.0,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = _make_service(food_search=mock_search, session=MagicMock())

        # 200g of rice: 130*2=260 kcal
        ing = make_ingredient(name="Ryz", amount_grams=200.0, kcal=0, auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        enriched = result.ingredients[0]
        assert enriched.kcal == 260.0  # 130 * (200/100)
        assert enriched.protein == 5.4  # 2.7 * 2
        assert enriched.fat == 0.6  # 0.3 * 2
        assert enriched.carbs == 56.0  # 28 * 2

    @pytest.mark.asyncio
    async def test_recalculates_meal_totals_after_enrichment(self):
        product = {
            "id": str(uuid4()),
            "name": "Ryz",
            "kcal_per_100g": 100,
            "protein_per_100g": 10.0,
            "fat_per_100g": 5.0,
            "carbs_per_100g": 20.0,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = _make_service(food_search=mock_search, session=MagicMock())

        # Existing matched ingredient
        ing1 = make_ingredient(name="A", kcal=200, protein=20, fat=10, carbs=30)
        # Unmatched ingredient (will be enriched)
        ing2 = make_ingredient(name="B", amount_grams=100, kcal=0, protein=0, fat=0, carbs=0, auto_food_id=False)
        meal = make_meal(ingredients=[ing1, ing2], total_kcal=200)

        result = await service._enrich_meal_ingredients(meal)

        # After enrichment: A(200kcal) + B(100kcal) = 300
        assert result.total_kcal == 300.0
        assert result.total_protein == 30.0  # 20 + 10
        assert result.total_fat == 15.0  # 10 + 5
        assert result.total_carbs == 50.0  # 30 + 20

    @pytest.mark.asyncio
    async def test_preserves_original_when_product_not_found(self):
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=None)
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Tajemniczy", kcal=50, auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        # No enrichment happened -> same meal returned
        assert result is meal

    @pytest.mark.asyncio
    async def test_returns_original_when_all_have_food_id(self):
        mock_search = AsyncMock()
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing1 = make_ingredient(name="A")
        ing2 = make_ingredient(name="B")
        meal = make_meal(ingredients=[ing1, ing2])

        result = await service._enrich_meal_ingredients(meal)

        assert result is meal
        mock_search.find_product_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_original_when_food_search_none(self):
        service = _make_service(food_search=None, session=MagicMock())

        ing = make_ingredient(name="Test", auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        assert result is meal

    @pytest.mark.asyncio
    async def test_returns_original_when_session_none(self):
        mock_search = AsyncMock()
        service = _make_service(food_search=mock_search, session=None)

        ing = make_ingredient(name="Test", auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        assert result is meal

    @pytest.mark.asyncio
    async def test_handles_product_id_as_uuid(self):
        product_id = uuid4()
        product = {
            "id": product_id,  # Already a UUID
            "name": "Test",
            "kcal_per_100g": 100,
            "protein_per_100g": 10,
            "fat_per_100g": 5,
            "carbs_per_100g": 20,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Test", auto_food_id=False)
        meal = make_meal(ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        assert result.ingredients[0].food_id == product_id

    @pytest.mark.asyncio
    async def test_meal_type_and_name_preserved(self):
        product = {
            "id": str(uuid4()),
            "name": "DB Name",
            "kcal_per_100g": 100,
            "protein_per_100g": 10,
            "fat_per_100g": 5,
            "carbs_per_100g": 20,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = _make_service(food_search=mock_search, session=MagicMock())

        ing = make_ingredient(name="Test", auto_food_id=False)
        meal = make_meal(meal_type="dinner", name="Kolacja testowa", ingredients=[ing])

        result = await service._enrich_meal_ingredients(meal)

        assert result.meal_type == "dinner"
        assert result.name == "Kolacja testowa"
