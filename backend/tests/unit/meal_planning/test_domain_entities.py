"""
Unit tests for meal planning domain entities.

Tests GeneratedDay computed properties and PlanPreferences defaults.
"""
import pytest

from src.meal_planning.domain.entities import (
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
    PlanPreferences,
)
from tests.unit.meal_planning.conftest import make_meal, make_ingredient


# ---------------------------------------------------------------------------
# GeneratedDay computed properties
# ---------------------------------------------------------------------------

class TestGeneratedDayProperties:
    """Tests for GeneratedDay total_kcal, total_protein, total_fat, total_carbs."""

    def test_total_kcal_sums_meal_totals(self):
        meals = [
            make_meal(total_kcal=500),
            make_meal(total_kcal=700),
            make_meal(total_kcal=300),
        ]
        day = GeneratedDay(day_number=1, meals=meals)
        assert day.total_kcal == 1500

    def test_total_protein_sums_meal_totals(self):
        ing1 = make_ingredient(protein=20)
        ing2 = make_ingredient(protein=30)
        meals = [make_meal(ingredients=[ing1]), make_meal(ingredients=[ing2])]
        day = GeneratedDay(day_number=1, meals=meals)
        assert day.total_protein == 50

    def test_total_fat_sums_meal_totals(self):
        ing1 = make_ingredient(fat=10)
        ing2 = make_ingredient(fat=15)
        meals = [make_meal(ingredients=[ing1]), make_meal(ingredients=[ing2])]
        day = GeneratedDay(day_number=1, meals=meals)
        assert day.total_fat == 25

    def test_total_carbs_sums_meal_totals(self):
        ing1 = make_ingredient(carbs=40)
        ing2 = make_ingredient(carbs=60)
        meals = [make_meal(ingredients=[ing1]), make_meal(ingredients=[ing2])]
        day = GeneratedDay(day_number=1, meals=meals)
        assert day.total_carbs == 100

    def test_empty_meals_returns_zero(self):
        day = GeneratedDay(day_number=1, meals=[])
        assert day.total_kcal == 0
        assert day.total_protein == 0
        assert day.total_fat == 0
        assert day.total_carbs == 0

    def test_single_meal_returns_meal_total(self):
        meal = make_meal(total_kcal=800)
        day = GeneratedDay(day_number=1, meals=[meal])
        assert day.total_kcal == 800


# ---------------------------------------------------------------------------
# PlanPreferences defaults
# ---------------------------------------------------------------------------

class TestPlanPreferencesDefaults:
    """Tests for PlanPreferences default values."""

    def test_diet_defaults_to_none(self):
        prefs = PlanPreferences()
        assert prefs.diet is None

    def test_allergies_defaults_to_empty_list(self):
        prefs = PlanPreferences()
        assert prefs.allergies == []

    def test_cuisine_defaults_to_polish(self):
        prefs = PlanPreferences()
        assert prefs.cuisine_preferences == ["polish"]

    def test_excluded_ingredients_defaults_to_empty_list(self):
        prefs = PlanPreferences()
        assert prefs.excluded_ingredients == []

    def test_max_preparation_time_defaults_to_none(self):
        prefs = PlanPreferences()
        assert prefs.max_preparation_time is None

    def test_default_lists_are_independent_between_instances(self):
        # Verify dataclass field(default_factory=...) is used correctly
        p1 = PlanPreferences()
        p2 = PlanPreferences()
        p1.allergies.append("gluten")
        assert "gluten" not in p2.allergies
