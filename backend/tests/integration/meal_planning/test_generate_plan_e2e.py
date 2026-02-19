"""
End-to-end integration tests for the full meal plan generation pipeline.

Uses mocked LLM but real service + adapter logic to verify the complete
flow from user profile to validated plan.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import (
    make_user_data, make_template, make_meal, make_ingredient, make_product,
)


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_planner():
    planner = AsyncMock()
    # 2 days x 2 meals each
    planner.generate_meal_templates = AsyncMock(
        return_value=[
            [make_template("breakfast", description="Owsianka"), make_template("lunch", description="Kurczak")],
            [make_template("breakfast", description="Jajecznica"), make_template("lunch", description="Ryba")],
        ]
    )
    # Each call returns a meal with ingredients that have food_ids
    planner.generate_meal = AsyncMock(
        side_effect=lambda **kwargs: make_meal(
            meal_type=kwargs["template"].meal_type,
            name=kwargs["template"].description,
            ingredients=[
                make_ingredient(name=f"Ing_{kwargs['template'].meal_type}_1", kcal=300),
                make_ingredient(name=f"Ing_{kwargs['template'].meal_type}_2", kcal=200),
            ]
        )
    )
    planner.optimize_plan = AsyncMock(side_effect=lambda days, profile: days)
    return planner


@pytest.fixture
def mock_food_search():
    search = AsyncMock()
    search.search_for_meal_planning = AsyncMock(
        return_value=[make_product(name="Generic"), make_product(name="Other")]
    )
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


class TestGeneratePlanE2EIndexed:
    """End-to-end tests for full generation pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_valid_plan(self, service):
        user = make_user_data()
        prefs = PlanPreferences()

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=2)

        # Plan structure
        assert len(plan.days) == 2
        for day in plan.days:
            assert len(day.meals) == 2
            for meal in day.meals:
                assert len(meal.ingredients) == 2
                for ing in meal.ingredients:
                    assert ing.food_id is not None

        # Metadata
        assert "quality_validation" in plan.generation_metadata
        assert plan.generation_metadata["days_generated"] == 2

    @pytest.mark.asyncio
    async def test_used_ingredients_accumulate_across_days(self, service, mock_planner):
        user = make_user_data()
        prefs = PlanPreferences()

        # Capture snapshots of used_ingredients at each call, since the list
        # is passed by reference and mutated after the mock records it.
        used_snapshots = []
        original_side_effect = mock_planner.generate_meal.side_effect

        async def tracking_side_effect(**kwargs):
            used_snapshots.append(list(kwargs["used_ingredients"]))  # copy
            return await original_side_effect(**kwargs) if not callable(original_side_effect) else original_side_effect(**kwargs)

        mock_planner.generate_meal.side_effect = tracking_side_effect

        await service.generate_plan(user, prefs, date(2026, 1, 1), days=2)

        # 4 meals total (2 days x 2 meals)
        assert len(used_snapshots) == 4

        # First call: empty used list
        assert len(used_snapshots[0]) == 0

        # Last call: should have ingredients from previous meals
        assert len(used_snapshots[3]) > 0

        # Used ingredients should monotonically increase
        for i in range(1, len(used_snapshots)):
            assert len(used_snapshots[i]) >= len(used_snapshots[i - 1])

    @pytest.mark.asyncio
    async def test_progress_callback_reports_all_stages(self, service):
        user = make_user_data()
        prefs = PlanPreferences()
        updates = []

        async def cb(update):
            updates.append(update)

        await service.generate_plan(user, prefs, date(2026, 1, 1), days=2, progress_callback=cb)

        stages = [u["stage"] for u in updates]
        assert stages[0] == "profile"
        assert "templates" in stages
        assert "generating" in stages
        assert "optimizing" in stages
        assert stages[-1] == "complete"

        # Progress monotonically increases
        progress_values = [u["progress"] for u in updates]
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1]

    @pytest.mark.asyncio
    async def test_plan_with_allergies_forwards_preferences(self, service, mock_food_search):
        user = make_user_data()
        prefs = PlanPreferences(
            diet="vegetarian",
            allergies=["orzechy", "gluten"],
        )

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=2)

        # All search calls should include allergy info
        for call in mock_food_search.search_for_meal_planning.call_args_list:
            p = call.kwargs["preferences"]
            assert "orzechy" in p["allergies"]
            assert "gluten" in p["allergies"]
            assert p["diet"] == "vegetarian"

        # Plan records applied preferences
        assert plan.preferences_applied["diet"] == "vegetarian"
        assert plan.preferences_applied["allergies"] == ["orzechy", "gluten"]

    @pytest.mark.asyncio
    async def test_plan_has_daily_targets_in_metadata(self, service):
        user = make_user_data()
        prefs = PlanPreferences()

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1))

        targets = plan.generation_metadata["daily_targets"]
        assert "kcal" in targets
        assert "protein" in targets
        assert "fat" in targets
        assert "carbs" in targets
        assert targets["kcal"] > 0

    @pytest.mark.asyncio
    async def test_quality_validation_present(self, service):
        user = make_user_data()
        prefs = PlanPreferences()

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1))

        validation = plan.generation_metadata["quality_validation"]
        assert "food_id_percentage" in validation
        assert "calorie_deviation_days" in validation
        assert "empty_meals" in validation
        assert "is_valid" in validation
        assert validation["food_id_percentage"] == 100.0
        assert validation["empty_meals"] == []
