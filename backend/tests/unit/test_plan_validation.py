"""
Unit tests for meal plan quality validation.

Tests the validate_plan_quality method in MealPlanService that checks
ingredient matching, calorie deviation, and empty meals.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import (
    GeneratedPlan,
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
)


@pytest.fixture
def service():
    """Create service instance with mocked repository."""
    mock_repo = MagicMock()
    return MealPlanService(repository=mock_repo)


def make_ingredient(
    name: str = "Test",
    food_id: UUID = None,
    amount_grams: float = 100,
    kcal: float = 100,
) -> GeneratedIngredient:
    """Helper to create test ingredient."""
    return GeneratedIngredient(
        food_id=food_id or uuid4(),
        name=name,
        amount_grams=amount_grams,
        unit_label=None,
        kcal=kcal,
        protein=10.0,
        fat=5.0,
        carbs=15.0,
    )


def make_meal(
    meal_type: str = "breakfast",
    ingredients: list = None,
    total_kcal: float = None,
) -> GeneratedMeal:
    """Helper to create test meal."""
    if ingredients is None:
        ingredients = [make_ingredient()]
    if total_kcal is None:
        total_kcal = sum(i.kcal for i in ingredients)
    return GeneratedMeal(
        meal_type=meal_type,
        name="Test Meal",
        description="Test",
        preparation_time_minutes=15,
        ingredients=ingredients,
        total_kcal=total_kcal,
        total_protein=sum(i.protein for i in ingredients),
        total_fat=sum(i.fat for i in ingredients),
        total_carbs=sum(i.carbs for i in ingredients),
    )


def make_day(day_number: int = 1, meals: list = None) -> GeneratedDay:
    """Helper to create test day."""
    if meals is None:
        meals = [
            make_meal("breakfast", total_kcal=500),
            make_meal("lunch", total_kcal=700),
            make_meal("dinner", total_kcal=400),
        ]
    return GeneratedDay(day_number=day_number, meals=meals)


def make_plan(days: list = None) -> GeneratedPlan:
    """Helper to create test plan."""
    if days is None:
        days = [make_day(1), make_day(2)]
    return GeneratedPlan(
        days=days,
        preferences_applied={},
        generation_metadata={},
    )


class TestFoodIdPercentage:
    """Tests for food_id matching percentage validation."""

    def test_100_percent_when_all_have_food_id(self, service):
        """Should report 100% when all ingredients have food_id."""
        plan = make_plan()
        result = service.validate_plan_quality(plan, 2000)

        assert result["food_id_percentage"] == 100.0
        assert result["is_valid"] is True

    def test_0_percent_when_none_have_food_id(self, service):
        """Should report 0% when no ingredients have food_id."""
        ing = make_ingredient()
        ing.food_id = None  # No food_id

        meal = make_meal(ingredients=[ing])
        day = make_day(meals=[meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["food_id_percentage"] == 0.0
        assert result["is_valid"] is False

    def test_partial_percentage(self, service):
        """Should calculate correct percentage for mixed ingredients."""
        ing_with = make_ingredient(name="With ID")
        ing_without = make_ingredient(name="Without ID")
        ing_without.food_id = None

        meal = make_meal(ingredients=[ing_with, ing_without])
        day = make_day(meals=[meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["food_id_percentage"] == 50.0
        assert result["total_ingredients"] == 2
        assert result["ingredients_with_food_id"] == 1


class TestCalorieDeviation:
    """Tests for daily calorie deviation validation."""

    def test_no_deviation_when_on_target(self, service):
        """Should report no deviation when calories are on target."""
        # Create day with exactly 2000 kcal
        meals = [
            make_meal("breakfast", total_kcal=500),
            make_meal("lunch", total_kcal=700),
            make_meal("dinner", total_kcal=800),
        ]
        day = make_day(meals=meals)  # Total: 2000 kcal
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["calorie_deviation_days"] == []

    def test_flags_deviation_below_80_percent(self, service):
        """Should flag days below 80% of target."""
        # Create day with only 1500 kcal (75% of 2000)
        meals = [
            make_meal("breakfast", total_kcal=500),
            make_meal("lunch", total_kcal=500),
            make_meal("dinner", total_kcal=500),
        ]
        day = make_day(meals=meals)  # Total: 1500 kcal
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert 1 in result["calorie_deviation_days"]
        assert len(result["issues"]) > 0

    def test_flags_deviation_above_120_percent(self, service):
        """Should flag days above 120% of target."""
        # Create day with 2500 kcal (125% of 2000)
        meals = [
            make_meal("breakfast", total_kcal=800),
            make_meal("lunch", total_kcal=900),
            make_meal("dinner", total_kcal=800),
        ]
        day = make_day(meals=meals)  # Total: 2500 kcal
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert 1 in result["calorie_deviation_days"]

    def test_allows_90_percent(self, service):
        """Should allow 90% of target (within 80-120%)."""
        # Create day with 1800 kcal (90% of 2000)
        meals = [
            make_meal("breakfast", total_kcal=600),
            make_meal("lunch", total_kcal=600),
            make_meal("dinner", total_kcal=600),
        ]
        day = make_day(meals=meals)  # Total: 1800 kcal
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["calorie_deviation_days"] == []


class TestEmptyMeals:
    """Tests for empty meals detection."""

    def test_detects_empty_meal(self, service):
        """Should detect meals with no ingredients."""
        empty_meal = make_meal(ingredients=[])
        day = make_day(meals=[empty_meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert len(result["empty_meals"]) == 1
        assert result["empty_meals"][0] == (1, "breakfast")
        assert result["is_valid"] is False

    def test_no_empty_meals_when_all_have_ingredients(self, service):
        """Should report no empty meals when all have ingredients."""
        plan = make_plan()
        result = service.validate_plan_quality(plan, 2000)

        assert result["empty_meals"] == []


class TestIsValidFlag:
    """Tests for overall is_valid determination."""

    def test_valid_when_all_criteria_pass(self, service):
        """Should be valid when all quality criteria pass."""
        plan = make_plan()
        result = service.validate_plan_quality(plan, 1600)

        assert result["is_valid"] is True

    def test_invalid_when_food_id_below_90_percent(self, service):
        """Should be invalid when food_id percentage is below 90%."""
        # Create ingredients where less than 90% have food_id
        ingredients = [make_ingredient() for _ in range(10)]
        # Set food_id to None for 2 ingredients (80% matching)
        ingredients[0].food_id = None
        ingredients[1].food_id = None

        meal = make_meal(ingredients=ingredients)
        day = make_day(meals=[meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["food_id_percentage"] == 80.0
        assert result["is_valid"] is False

    def test_invalid_when_empty_meals_exist(self, service):
        """Should be invalid when any meal has no ingredients."""
        normal_meal = make_meal()
        empty_meal = make_meal(ingredients=[])

        day = make_day(meals=[normal_meal, empty_meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert result["is_valid"] is False

    def test_allows_some_calorie_deviation(self, service):
        """Should allow up to half of days with calorie deviation."""
        # 2 days: 1 on target, 1 off target = valid
        day_good = make_day(
            day_number=1,
            meals=[make_meal(total_kcal=2000)]
        )
        day_bad = make_day(
            day_number=2,
            meals=[make_meal(total_kcal=1000)]  # 50% - way off
        )
        plan = make_plan(days=[day_good, day_bad])

        result = service.validate_plan_quality(plan, 2000)

        # 1 out of 2 days off = exactly half, should still be valid
        assert result["is_valid"] is True

    def test_invalid_when_most_days_off_target(self, service):
        """Should be invalid when more than half of days are off target."""
        # 3 days: 1 on target, 2 off target = invalid
        day_good = make_day(
            day_number=1,
            meals=[make_meal(total_kcal=2000)]
        )
        day_bad1 = make_day(
            day_number=2,
            meals=[make_meal(total_kcal=1000)]
        )
        day_bad2 = make_day(
            day_number=3,
            meals=[make_meal(total_kcal=1000)]
        )
        plan = make_plan(days=[day_good, day_bad1, day_bad2])

        result = service.validate_plan_quality(plan, 2000)

        # 2 out of 3 days off > half, should be invalid
        assert result["is_valid"] is False


class TestIssuesReporting:
    """Tests for human-readable issues list."""

    def test_reports_missing_food_id(self, service):
        """Should include issue for ingredients without food_id."""
        ing = make_ingredient(name="Tajemniczy skladnik")
        ing.food_id = None

        meal = make_meal(meal_type="lunch", ingredients=[ing])
        day = make_day(meals=[meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert any("Tajemniczy skladnik" in issue for issue in result["issues"])
        assert any("bez food_id" in issue for issue in result["issues"])

    def test_reports_calorie_deviation(self, service):
        """Should include issue for calorie deviation."""
        meals = [make_meal(total_kcal=1000)]  # 50% of 2000
        day = make_day(meals=meals)
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert any("1000 kcal" in issue for issue in result["issues"])
        assert any("50%" in issue for issue in result["issues"])

    def test_reports_empty_meal(self, service):
        """Should include issue for empty meal."""
        empty_meal = make_meal(meal_type="snack", ingredients=[])
        day = make_day(meals=[empty_meal])
        plan = make_plan(days=[day])

        result = service.validate_plan_quality(plan, 2000)

        assert any("snack" in issue for issue in result["issues"])
        assert any("brak skladnikow" in issue for issue in result["issues"])
