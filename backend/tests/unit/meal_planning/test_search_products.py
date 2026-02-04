"""
Unit tests for MealPlanService._search_products_for_meal.

Verifies that allergies, diet, and excluded ingredients are correctly
forwarded to the food search service. This is the gateway for allergy
enforcement — if preferences are dropped here, allergens leak into plans.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import make_template, make_product


@pytest.fixture
def mock_food_search():
    search = AsyncMock()
    search.search_for_meal_planning = AsyncMock(return_value=[])
    return search


@pytest.fixture
def mock_session():
    return MagicMock()


def _make_service(food_search=None, session=None):
    return MealPlanService(
        repository=MagicMock(),
        food_search=food_search,
        session=session,
    )


class TestSearchProductsForMeal:
    """Tests for _search_products_for_meal preference forwarding."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_food_search_not_configured(self, mock_session):
        service = _make_service(food_search=None, session=mock_session)
        template = make_template()
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_session_not_provided(self, mock_food_search):
        service = _make_service(food_search=mock_food_search, session=None)
        template = make_template()
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        assert result == []

    @pytest.mark.asyncio
    async def test_calls_search_with_correct_meal_type(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(meal_type="lunch")
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["meal_type"] == "lunch"

    @pytest.mark.asyncio
    async def test_passes_allergies_in_preferences(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences(allergies=["gluten", "laktoza"])

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        passed_prefs = call_kwargs.kwargs["preferences"]
        assert passed_prefs["allergies"] == ["gluten", "laktoza"]

    @pytest.mark.asyncio
    async def test_passes_diet_in_preferences(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences(diet="vegan")

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        passed_prefs = call_kwargs.kwargs["preferences"]
        assert passed_prefs["diet"] == "vegan"

    @pytest.mark.asyncio
    async def test_passes_excluded_ingredients_in_preferences(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences(excluded_ingredients=["cukier", "sol"])

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        passed_prefs = call_kwargs.kwargs["preferences"]
        assert passed_prefs["excluded_ingredients"] == ["cukier", "sol"]

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs, limit=25)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["limit"] == 25

    @pytest.mark.asyncio
    async def test_default_limit_is_15(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["limit"] == 15

    @pytest.mark.asyncio
    async def test_returns_products_from_food_search(self, mock_food_search, mock_session):
        products = [make_product(name="A"), make_product(name="B")]
        mock_food_search.search_for_meal_planning = AsyncMock(return_value=products)
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        assert len(result) == 2
        assert result[0]["name"] == "A"

    @pytest.mark.asyncio
    async def test_passes_session_to_food_search(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template()
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["session"] is mock_session

    @pytest.mark.asyncio
    async def test_passes_meal_description_from_template(self, mock_food_search, mock_session):
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(description="Owsianka z bananem i migdalami")
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["meal_description"] == "Owsianka z bananem i migdalami"
