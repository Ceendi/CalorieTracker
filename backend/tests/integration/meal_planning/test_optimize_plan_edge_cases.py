"""
Integration tests for BielikMealPlannerAdapter.optimize_plan edge cases.

Tests scaling behavior: floor/ceiling limits, zero-calorie days,
nutrient proportional scaling, and independent day scaling.
"""
import pytest
from uuid import uuid4

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import (
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
    UserProfile,
)
from tests.unit.meal_planning.conftest import make_ingredient, make_meal, make_profile


@pytest.fixture
def adapter():
    a = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
    a._model = None
    a._embedding_service = None
    return a


def _make_day_with_kcal(kcal: float, day_number: int = 1) -> GeneratedDay:
    """Create a day with a single meal totaling the given kcal."""
    ing = GeneratedIngredient(
        food_id=uuid4(), name="Test", amount_grams=100.0,
        unit_label=None, kcal=kcal, protein=kcal * 0.1,
        fat=kcal * 0.05, carbs=kcal * 0.15,
    )
    meal = GeneratedMeal(
        meal_type="lunch", name="Test Meal", description="Test",
        preparation_time_minutes=15, ingredients=[ing],
        total_kcal=kcal, total_protein=kcal * 0.1,
        total_fat=kcal * 0.05, total_carbs=kcal * 0.15,
    )
    return GeneratedDay(day_number=day_number, meals=[meal])


class TestOptimizePlanScaling:
    """Tests for plan optimization scaling behavior."""

    @pytest.mark.asyncio
    async def test_no_scaling_when_within_10_percent(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(1950)  # ratio 1.026, within 10%

        result = await adapter.optimize_plan([day], profile)

        assert result[0].meals[0].total_kcal == 1950  # Unchanged

    @pytest.mark.asyncio
    async def test_scales_up_when_below_target(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(1500)  # ratio 1.33

        result = await adapter.optimize_plan([day], profile)

        # Should be scaled up, close to 2000
        assert result[0].total_kcal > 1500
        assert abs(result[0].total_kcal - 2000) < 10

    @pytest.mark.asyncio
    async def test_scale_floor_at_0_85(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(3000)  # ratio 0.667 -> clamped to 0.85

        result = await adapter.optimize_plan([day], profile)

        # 3000 * 0.85 = 2550 (not 3000 * 0.667 = 2001)
        expected = 3000 * 0.85
        assert abs(result[0].total_kcal - expected) < 1

    @pytest.mark.asyncio
    async def test_scale_ceiling_at_3_0(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(500)  # ratio 4.0 -> clamped to 3.0

        result = await adapter.optimize_plan([day], profile)

        # 500 * 3.0 = 1500 (not 500 * 4.0 = 2000)
        expected = 500 * 3.0
        assert abs(result[0].total_kcal - expected) < 1

    @pytest.mark.asyncio
    async def test_zero_calorie_day_no_division_by_zero(self, adapter):
        profile = make_profile(daily_kcal=2000)
        empty_meal = GeneratedMeal(
            meal_type="lunch", name="Empty", description="",
            preparation_time_minutes=0, ingredients=[],
            total_kcal=0, total_protein=0, total_fat=0, total_carbs=0,
        )
        day = GeneratedDay(day_number=1, meals=[empty_meal])

        # Should not raise ZeroDivisionError
        result = await adapter.optimize_plan([day], profile)
        assert result[0].total_kcal == 0

    @pytest.mark.asyncio
    async def test_scaling_applied_to_all_nutrients(self, adapter):
        profile = make_profile(daily_kcal=2000)
        ing = GeneratedIngredient(
            food_id=uuid4(), name="Test", amount_grams=100.0,
            unit_label=None, kcal=1000, protein=50.0,
            fat=20.0, carbs=100.0,
        )
        meal = GeneratedMeal(
            meal_type="lunch", name="Test", description="",
            preparation_time_minutes=15, ingredients=[ing],
            total_kcal=1000, total_protein=50, total_fat=20, total_carbs=100,
        )
        day = GeneratedDay(day_number=1, meals=[meal])

        result = await adapter.optimize_plan([day], profile)

        # ratio = 2000/1000 = 2.0, scale = 2.0
        r_ing = result[0].meals[0].ingredients[0]
        assert abs(r_ing.amount_grams - 200.0) < 0.1
        assert abs(r_ing.protein - 100.0) < 0.1
        assert abs(r_ing.fat - 40.0) < 0.1
        assert abs(r_ing.carbs - 200.0) < 0.1

    @pytest.mark.asyncio
    async def test_scaling_applied_to_meal_totals(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(1000)

        result = await adapter.optimize_plan([day], profile)

        meal = result[0].meals[0]
        assert abs(meal.total_kcal - 2000) < 10
        assert meal.total_protein > 0

    @pytest.mark.asyncio
    async def test_multiple_days_scaled_independently(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day1 = _make_day_with_kcal(1500, day_number=1)  # Scale up
        day2 = _make_day_with_kcal(2500, day_number=2)  # Scale down (but floor at 0.85)

        result = await adapter.optimize_plan([day1, day2], profile)

        # Day 1: scaled up toward 2000
        assert result[0].total_kcal > 1500
        # Day 2: scaled down (2500 * 0.85 = 2125 since ratio 0.8 < 0.85 floor)
        assert result[1].total_kcal < 2500

    @pytest.mark.asyncio
    async def test_exact_target_no_scaling(self, adapter):
        profile = make_profile(daily_kcal=2000)
        day = _make_day_with_kcal(2000)

        result = await adapter.optimize_plan([day], profile)

        assert result[0].total_kcal == 2000  # ratio=1.0, abs(0) < 0.1
