"""
Unit tests for MealPlanService.generate_plan orchestration.

Tests the full generation flow: profile building, template generation,
meal generation with product search, enrichment, optimization, and
quality validation. Verifies used_ingredients tracking for variety.
"""
import pytest
from datetime import date
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import (
    make_user_data, make_template, make_meal, make_ingredient, make_day,
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
    meal_with_ing = make_meal(
        ingredients=[make_ingredient(name="IngA"), make_ingredient(name="IngB")]
    )
    planner.generate_meal = AsyncMock(return_value=meal_with_ing)
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


@pytest.fixture
def user():
    return make_user_data()


@pytest.fixture
def prefs():
    return PlanPreferences()


class TestGeneratePlanOrchestration:
    """Tests for generate_plan orchestration flow."""

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_planner_not_configured(self, mock_repo, user, prefs):
        service = MealPlanService(repository=mock_repo, planner=None)
        with pytest.raises(RuntimeError, match="Meal planner not configured"):
            await service.generate_plan(user, prefs, date(2026, 1, 1))

    @pytest.mark.asyncio
    async def test_calls_generate_meal_templates(self, service, mock_planner, user, prefs):
        await service.generate_plan(user, prefs, date(2026, 1, 1), days=3)

        mock_planner.generate_meal_templates.assert_called_once()
        call_args = mock_planner.generate_meal_templates.call_args
        assert call_args[0][1] == 3  # days parameter

    @pytest.mark.asyncio
    async def test_calls_generate_meal_for_each_template(self, service, mock_planner, user, prefs):
        # 1 day with 2 meals
        await service.generate_plan(user, prefs, date(2026, 1, 1))

        assert mock_planner.generate_meal.call_count == 2

    @pytest.mark.asyncio
    async def test_calls_optimize_plan(self, service, mock_planner, user, prefs):
        await service.generate_plan(user, prefs, date(2026, 1, 1))

        mock_planner.optimize_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_used_ingredients_accumulate_across_meals(self, service, mock_planner, user, prefs):
        # First call returns ingredient A, second returns B
        meal1 = make_meal(ingredients=[make_ingredient(name="IngA")])
        meal2 = make_meal(ingredients=[make_ingredient(name="IngB")])
        mock_planner.generate_meal = AsyncMock(side_effect=[meal1, meal2])

        await service.generate_plan(user, prefs, date(2026, 1, 1))

        # Second call should have received used_ingredients containing "IngA"
        second_call = mock_planner.generate_meal.call_args_list[1]
        used = second_call.kwargs["used_ingredients"]
        assert "IngA" in used

    @pytest.mark.asyncio
    async def test_progress_callback_called_at_each_stage(self, service, user, prefs):
        progress_updates = []

        async def callback(update):
            progress_updates.append(update)

        await service.generate_plan(user, prefs, date(2026, 1, 1), progress_callback=callback)

        stages = [u["stage"] for u in progress_updates]
        assert "profile" in stages
        assert "templates" in stages
        assert "generating" in stages
        assert "optimizing" in stages
        assert "complete" in stages

    @pytest.mark.asyncio
    async def test_progress_increases_monotonically(self, service, user, prefs):
        progress_values = []

        async def callback(update):
            progress_values.append(update.get("progress", 0))

        await service.generate_plan(user, prefs, date(2026, 1, 1), progress_callback=callback)

        # Progress should be non-decreasing
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1]

        assert progress_values[0] == 5
        assert progress_values[-1] == 100

    @pytest.mark.asyncio
    async def test_progress_callback_none_is_safe(self, service, user, prefs):
        # Should not raise with progress_callback=None
        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), progress_callback=None)
        assert plan is not None

    @pytest.mark.asyncio
    async def test_plan_has_correct_metadata(self, service, user, prefs):
        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=3)

        meta = plan.generation_metadata
        assert "daily_targets" in meta
        assert meta["days_generated"] == 3
        assert meta["start_date"] == "2026-01-01"

    @pytest.mark.asyncio
    async def test_plan_has_preferences_applied(self, service, user):
        prefs = PlanPreferences(diet="vegan", allergies=["gluten"])

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1))

        assert plan.preferences_applied["diet"] == "vegan"
        assert plan.preferences_applied["allergies"] == ["gluten"]

    @pytest.mark.asyncio
    async def test_validation_in_metadata(self, service, user, prefs):
        plan = await service.generate_plan(user, prefs, date(2026, 1, 1))

        assert "quality_validation" in plan.generation_metadata
        validation = plan.generation_metadata["quality_validation"]
        assert "food_id_percentage" in validation
        assert "is_valid" in validation

    @pytest.mark.asyncio
    async def test_correct_day_numbers_assigned(self, service, mock_planner, user, prefs):
        # 2 days
        mock_planner.generate_meal_templates = AsyncMock(
            return_value=[
                [make_template("breakfast")],
                [make_template("breakfast")],
            ]
        )

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=2)

        assert plan.days[0].day_number == 1
        assert plan.days[1].day_number == 2
