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


# ---------------------------------------------------------------------------
# Keyword-based search tests
# ---------------------------------------------------------------------------

class TestSearchProductsByKeywords:
    """Tests for _search_products_by_keywords and keyword-aware _search_products_for_meal."""

    @pytest.mark.asyncio
    async def test_uses_keywords_when_available(self, mock_food_search, mock_session):
        """When template has keywords, should search for each keyword separately."""
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            meal_type="dinner",
            description="Kanapki z twarogiem",
            ingredient_keywords=["chleb", "twarog", "rzodkiewka"],
        )
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        # Should be called 3 times - once per keyword
        assert mock_food_search.search_for_meal_planning.call_count == 3

        # Collect all meal_description values passed
        descriptions = [
            call.kwargs["meal_description"]
            for call in mock_food_search.search_for_meal_planning.call_args_list
        ]
        assert "chleb" in descriptions
        assert "twarog" in descriptions
        assert "rzodkiewka" in descriptions

    @pytest.mark.asyncio
    async def test_falls_back_to_description_when_no_keywords(self, mock_food_search, mock_session):
        """When template has no keywords, should use description-based search."""
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            description="Kanapki z twarogiem",
            ingredient_keywords=[],  # Empty keywords
        )
        prefs = PlanPreferences()

        await service._search_products_for_meal(template, prefs)

        # Should be called once with description
        assert mock_food_search.search_for_meal_planning.call_count == 1
        call_kwargs = mock_food_search.search_for_meal_planning.call_args
        assert call_kwargs.kwargs["meal_description"] == "Kanapki z twarogiem"

    @pytest.mark.asyncio
    async def test_deduplicates_products_from_multiple_keywords(self, mock_food_search, mock_session):
        """Products found by multiple keywords should appear only once."""
        # Same product returned for two different keywords
        product = make_product(id="dup-id", name="Chleb razowy")
        mock_food_search.search_for_meal_planning = AsyncMock(return_value=[product])

        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["chleb", "pieczywo"],
        )
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        # Should have only one product despite being returned twice
        assert len(result) == 1
        assert result[0]["name"] == "Chleb razowy"

    @pytest.mark.asyncio
    async def test_merges_products_from_different_keywords(self, mock_food_search, mock_session):
        """Products from different keywords should be merged."""
        bread = make_product(id="bread-id", name="Chleb", score=0.9)
        cheese = make_product(id="cheese-id", name="Twarog", score=0.8)

        # Return different products for each keyword
        call_count = [0]

        async def mock_search(**kwargs):
            call_count[0] += 1
            if "chleb" in kwargs.get("meal_description", ""):
                return [bread]
            elif "twarog" in kwargs.get("meal_description", ""):
                return [cheese]
            return []

        mock_food_search.search_for_meal_planning = mock_search

        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["chleb", "twarog"],
        )
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        # Should have both products
        assert len(result) == 2
        names = [p["name"] for p in result]
        assert "Chleb" in names
        assert "Twarog" in names

    @pytest.mark.asyncio
    async def test_sorts_merged_products_by_score(self, mock_food_search, mock_session):
        """Merged products should be sorted by score descending."""
        low_score = make_product(id="low-id", name="Low", score=0.3)
        high_score = make_product(id="high-id", name="High", score=0.9)

        call_count = [0]

        async def mock_search(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [low_score]
            return [high_score]

        mock_food_search.search_for_meal_planning = mock_search

        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["first", "second"],
        )
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        # High score should be first
        assert result[0]["name"] == "High"
        assert result[1]["name"] == "Low"

    @pytest.mark.asyncio
    async def test_respects_limit_for_keyword_search(self, mock_food_search, mock_session):
        """Keyword search should respect the limit parameter."""
        products = [make_product(id=f"id-{i}", name=f"Product {i}") for i in range(20)]
        mock_food_search.search_for_meal_planning = AsyncMock(return_value=products)

        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["a", "b"],
        )
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs, limit=10)

        # Should respect the limit
        assert len(result) <= 10

    @pytest.mark.asyncio
    async def test_passes_preferences_to_each_keyword_search(self, mock_food_search, mock_session):
        """Preferences should be passed to each keyword search."""
        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["a", "b"],
        )
        prefs = PlanPreferences(allergies=["gluten"], diet="vegan")

        await service._search_products_for_meal(template, prefs)

        # All calls should have the same preferences
        for call in mock_food_search.search_for_meal_planning.call_args_list:
            passed_prefs = call.kwargs["preferences"]
            assert passed_prefs["allergies"] == ["gluten"]
            assert passed_prefs["diet"] == "vegan"

    @pytest.mark.asyncio
    async def test_handles_empty_results_from_keyword(self, mock_food_search, mock_session):
        """Empty results from one keyword should not break the search."""
        product = make_product(name="Found")

        async def mock_search(**kwargs):
            if "found" in kwargs.get("meal_description", ""):
                return [product]
            return []  # Empty for other keywords

        mock_food_search.search_for_meal_planning = mock_search

        service = _make_service(food_search=mock_food_search, session=mock_session)
        template = make_template(
            ingredient_keywords=["notfound", "found"],
        )
        prefs = PlanPreferences()

        result = await service._search_products_for_meal(template, prefs)

        # Should still return the product from the working keyword
        assert len(result) == 1
        assert result[0]["name"] == "Found"
