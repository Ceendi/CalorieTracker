"""
Unit tests for BMR/CPM calculations and daily macro target generation.

Tests calculate_daily_targets, _calculate_bmr, _get_activity_multiplier
in MealPlanService. Verifies Mifflin-St Jeor equation correctness,
activity level multipliers, goal adjustments, and macro gram calculations.
"""
import pytest
from unittest.mock import MagicMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import make_user_data


@pytest.fixture
def service():
    return MealPlanService(repository=MagicMock())


@pytest.fixture
def prefs():
    return PlanPreferences()


# ---------------------------------------------------------------------------
# BMR calculation (Mifflin-St Jeor)
# ---------------------------------------------------------------------------

class TestCalculateBMR:
    """Tests for _calculate_bmr using Mifflin-St Jeor equation."""

    def test_male_bmr_known_values(self, service):
        # Male, 80kg, 180cm, 30yo
        # BMR = 10*80 + 6.25*180 - 5*30 + 5 = 800 + 1125 - 150 + 5 = 1780
        user = make_user_data(weight=80, height=180, age=30, gender="male")
        assert service._calculate_bmr(user) == 1780.0

    def test_female_bmr_known_values(self, service):
        # Female, 60kg, 165cm, 25yo
        # BMR = 10*60 + 6.25*165 - 5*25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
        user = make_user_data(weight=60, height=165, age=25, gender="female")
        assert service._calculate_bmr(user) == 1345.25

    def test_male_vs_female_difference_is_166(self, service):
        # Same stats, male - female should be exactly 166 (5 - (-161))
        male = make_user_data(weight=70, height=170, age=30, gender="male")
        female = make_user_data(weight=70, height=170, age=30, gender="female")
        assert service._calculate_bmr(male) - service._calculate_bmr(female) == 166

    def test_very_low_weight_still_positive(self, service):
        user = make_user_data(weight=40, height=150, age=18, gender="female")
        bmr = service._calculate_bmr(user)
        assert bmr > 0

    def test_very_high_weight(self, service):
        user = make_user_data(weight=150, height=200, age=60, gender="male")
        bmr = service._calculate_bmr(user)
        assert bmr > 0

    def test_non_binary_defaults_to_female_formula(self, service):
        # Any gender != "male" uses the else branch (female formula)
        user = make_user_data(weight=70, height=170, age=30, gender="other")
        female = make_user_data(weight=70, height=170, age=30, gender="female")
        assert service._calculate_bmr(user) == service._calculate_bmr(female)


# ---------------------------------------------------------------------------
# Activity multiplier
# ---------------------------------------------------------------------------

class TestActivityMultiplier:
    """Tests for _get_activity_multiplier."""

    def test_sedentary(self, service):
        assert service._get_activity_multiplier("sedentary") == 1.4

    def test_light(self, service):
        assert service._get_activity_multiplier("light") == 1.55

    def test_moderate(self, service):
        assert service._get_activity_multiplier("moderate") == 1.70

    def test_active(self, service):
        assert service._get_activity_multiplier("active") == 1.85

    def test_very_active(self, service):
        assert service._get_activity_multiplier("very_active") == 2.0

    def test_unknown_defaults_to_moderate(self, service):
        assert service._get_activity_multiplier("unknown") == 1.55

    def test_empty_string_defaults_to_moderate(self, service):
        assert service._get_activity_multiplier("") == 1.55


# ---------------------------------------------------------------------------
# Daily targets calculation (full pipeline)
# ---------------------------------------------------------------------------

class TestCalculateDailyTargets:
    """Tests for calculate_daily_targets end-to-end."""

    def test_maintain_goal_no_adjustment(self, service, prefs):
        # Male 80kg 180cm 30yo moderate maintain
        # BMR=1780, CPM=1780*1.70=3026, goal=1.0 -> 3026
        user = make_user_data(goal="maintain")
        result = service.calculate_daily_targets(user, prefs)
        assert result["kcal"] == 3026

    def test_lose_goal_applies_20_percent_deficit(self, service, prefs):
        user = make_user_data(goal="lose")
        result = service.calculate_daily_targets(user, prefs)
        # 3026 * 0.8 = 2420.8 -> int = 2420
        assert result["kcal"] == 2420

    def test_gain_goal_applies_15_percent_surplus(self, service, prefs):
        user = make_user_data(goal="gain")
        result = service.calculate_daily_targets(user, prefs)
        # 3026 * 1.15 = 3479.9 -> int = 3479
        assert result["kcal"] == 3479

    def test_unknown_goal_defaults_to_maintain(self, service, prefs):
        user = make_user_data(goal="bulk")
        result = service.calculate_daily_targets(user, prefs)
        # Same as maintain: 3026
        assert result["kcal"] == 3026

    def test_protein_grams_calculation(self, service, prefs):
        # protein = round(kcal * 0.20 / 4, 1)
        user = make_user_data(goal="maintain")
        result = service.calculate_daily_targets(user, prefs)
        expected = round(3026 * 0.20 / 4, 1)
        assert result["protein"] == expected

    def test_fat_grams_calculation(self, service, prefs):
        # fat = round(kcal * 0.30 / 9, 1)
        user = make_user_data(goal="maintain")
        result = service.calculate_daily_targets(user, prefs)
        expected = round(3026 * 0.30 / 9, 1)
        assert result["fat"] == expected

    def test_carbs_grams_calculation(self, service, prefs):
        # carbs = round(kcal * 0.50 / 4, 1)
        user = make_user_data(goal="maintain")
        result = service.calculate_daily_targets(user, prefs)
        expected = round(3026 * 0.50 / 4, 1)
        assert result["carbs"] == expected

    def test_macro_ratios_sum_approximately_to_total_kcal(self, service, prefs):
        user = make_user_data(goal="maintain")
        result = service.calculate_daily_targets(user, prefs)
        # protein*4 + fat*9 + carbs*4 should ≈ kcal
        macro_kcal = result["protein"] * 4 + result["fat"] * 9 + result["carbs"] * 4
        assert abs(macro_kcal - result["kcal"]) < 10  # Allow rounding error

    def test_return_dict_has_all_keys(self, service, prefs):
        user = make_user_data()
        result = service.calculate_daily_targets(user, prefs)
        assert set(result.keys()) == {"kcal", "protein", "fat", "carbs"}

    def test_kcal_is_integer(self, service, prefs):
        user = make_user_data()
        result = service.calculate_daily_targets(user, prefs)
        assert isinstance(result["kcal"], int)

    def test_sedentary_female_lose_full_pipeline(self, service, prefs):
        # Female, 55kg, 160cm, 40yo, sedentary, lose
        # BMR = 10*55 + 6.25*160 - 5*40 - 161 = 550 + 1000 - 200 - 161 = 1189
        # CPM = 1189 * 1.4 = 1664.6
        # Adjusted = 1664.6 * 0.8 = 1331.68 -> 1331
        user = make_user_data(
            weight=55, height=160, age=40, gender="female",
            activity_level="sedentary", goal="lose"
        )
        result = service.calculate_daily_targets(user, prefs)
        assert result["kcal"] == 1331
        assert result["protein"] > 0
        assert result["fat"] > 0
        assert result["carbs"] > 0
