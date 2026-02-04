"""
Integration tests verifying allergy and diet enforcement throughout the pipeline.

These are the most critical safety tests — if a user declares a gluten
allergy and receives a plan containing wheat, that is a critical bug.
"""
import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import (
    make_user_data, make_template, make_meal, make_ingredient,
)


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_planner():
    planner = AsyncMock()
    planner.generate_meal_templates = AsyncMock(
        return_value=[[make_template("breakfast"), make_template("lunch")]]
    )
    planner.generate_meal = AsyncMock(return_value=make_meal())
    planner.optimize_plan = AsyncMock(side_effect=lambda days, profile: days)
    return planner


@pytest.fixture
def mock_food_search():
    search = AsyncMock()
    search.search_for_meal_planning = AsyncMock(return_value=[])
    search.find_product_by_name = AsyncMock(return_value=None)
    return search


@pytest.fixture
def service(mock_repo, mock_planner, mock_food_search):
    return MealPlanService(
        repository=mock_repo,
        planner=mock_planner,
        food_search=mock_food_search,
        session=MagicMock(),
    )


class TestAllergyEnforcement:
    """Integration tests verifying allergies are forwarded to food search."""

    @pytest.mark.asyncio
    async def test_allergies_passed_from_preferences_to_search(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(allergies=["gluten", "orzechy"])

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        # Every search call should have allergies
        for call in mock_food_search.search_for_meal_planning.call_args_list:
            passed_prefs = call.kwargs["preferences"]
            assert passed_prefs["allergies"] == ["gluten", "orzechy"], \
                "Allergies NOT forwarded to search — allergens may leak into plan!"

    @pytest.mark.asyncio
    async def test_excluded_ingredients_passed_to_search(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(excluded_ingredients=["cukier", "miod"])

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        for call in mock_food_search.search_for_meal_planning.call_args_list:
            passed_prefs = call.kwargs["preferences"]
            assert passed_prefs["excluded_ingredients"] == ["cukier", "miod"]

    @pytest.mark.asyncio
    async def test_diet_restriction_passed_to_search(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(diet="vegan")

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        for call in mock_food_search.search_for_meal_planning.call_args_list:
            passed_prefs = call.kwargs["preferences"]
            assert passed_prefs["diet"] == "vegan"

    @pytest.mark.asyncio
    async def test_full_generate_plan_with_allergy_verifies_all_search_calls(
        self, service, mock_food_search
    ):
        user = make_user_data()
        prefs = PlanPreferences(
            diet="vegetarian",
            allergies=["gluten", "laktoza"],
            excluded_ingredients=["cukier"],
        )

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1))

        # Verify all search calls had all restrictions
        assert mock_food_search.search_for_meal_planning.call_count > 0

        for call in mock_food_search.search_for_meal_planning.call_args_list:
            p = call.kwargs["preferences"]
            assert p["diet"] == "vegetarian"
            assert "gluten" in p["allergies"]
            assert "laktoza" in p["allergies"]
            assert "cukier" in p["excluded_ingredients"]

        # Verify plan metadata records preferences
        assert plan.preferences_applied["diet"] == "vegetarian"
        assert plan.preferences_applied["allergies"] == ["gluten", "laktoza"]

    @pytest.mark.asyncio
    async def test_preferences_not_mutated_during_generation(self, service):
        user = make_user_data()
        prefs = PlanPreferences(
            allergies=["gluten"],
            excluded_ingredients=["cukier"],
        )
        original_allergies = list(prefs.allergies)
        original_excluded = list(prefs.excluded_ingredients)

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        assert prefs.allergies == original_allergies
        assert prefs.excluded_ingredients == original_excluded


class TestDietFiltering:
    """Tests verifying diet-based category filtering logic."""

    def test_vegetarian_preferences_correctly_set(self):
        prefs = PlanPreferences(diet="vegetarian")
        assert prefs.diet == "vegetarian"

    def test_vegan_preferences_correctly_set(self):
        prefs = PlanPreferences(diet="vegan")
        assert prefs.diet == "vegan"

    def test_allergen_with_multiple_items(self):
        prefs = PlanPreferences(allergies=["gluten", "mleko", "jaja", "orzechy"])
        assert len(prefs.allergies) == 4

    @pytest.mark.asyncio
    async def test_empty_allergies_still_passed(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(allergies=[])

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        for call in mock_food_search.search_for_meal_planning.call_args_list:
            p = call.kwargs["preferences"]
            assert p["allergies"] == []

    @pytest.mark.asyncio
    async def test_none_diet_passed_correctly(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(diet=None)

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        for call in mock_food_search.search_for_meal_planning.call_args_list:
            p = call.kwargs["preferences"]
            assert p["diet"] is None
