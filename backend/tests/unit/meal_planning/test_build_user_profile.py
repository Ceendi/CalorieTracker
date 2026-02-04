"""
Unit tests for MealPlanService.build_user_profile.

Verifies that calculated targets and user preferences are correctly
combined into a UserProfile entity, especially that allergies and
excluded ingredients are not dropped.
"""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import make_user_data


@pytest.fixture
def service():
    return MealPlanService(repository=MagicMock())


class TestBuildUserProfile:
    """Tests for build_user_profile."""

    def test_profile_has_correct_daily_kcal(self, service):
        user = make_user_data(weight=80, height=180, age=30, gender="male",
                              activity_level="moderate", goal="maintain")
        prefs = PlanPreferences()

        profile = service.build_user_profile(user, prefs)

        assert profile.daily_kcal == 2759

    def test_profile_has_correct_macros(self, service):
        user = make_user_data(goal="maintain")
        prefs = PlanPreferences()

        profile = service.build_user_profile(user, prefs)

        assert profile.daily_protein == round(2759 * 0.30 / 4, 1)
        assert profile.daily_fat == round(2759 * 0.25 / 9, 1)
        assert profile.daily_carbs == round(2759 * 0.45 / 4, 1)

    def test_profile_includes_user_id(self, service):
        user_id = uuid4()
        user = make_user_data(id=user_id)
        prefs = PlanPreferences()

        profile = service.build_user_profile(user, prefs)

        assert profile.user_id == user_id

    def test_profile_preferences_contains_diet(self, service):
        user = make_user_data()
        prefs = PlanPreferences(diet="vegan")

        profile = service.build_user_profile(user, prefs)

        assert profile.preferences["diet"] == "vegan"

    def test_profile_preferences_contains_allergies(self, service):
        user = make_user_data()
        prefs = PlanPreferences(allergies=["gluten", "laktoza"])

        profile = service.build_user_profile(user, prefs)

        assert profile.preferences["allergies"] == ["gluten", "laktoza"]

    def test_profile_preferences_contains_cuisine(self, service):
        user = make_user_data()
        prefs = PlanPreferences(cuisine_preferences=["polska", "wloska"])

        profile = service.build_user_profile(user, prefs)

        assert profile.preferences["cuisine_preferences"] == ["polska", "wloska"]

    def test_profile_preferences_contains_excluded_ingredients(self, service):
        user = make_user_data()
        prefs = PlanPreferences(excluded_ingredients=["cukier", "sol"])

        profile = service.build_user_profile(user, prefs)

        assert profile.preferences["excluded_ingredients"] == ["cukier", "sol"]

    def test_profile_preferences_empty_when_defaults(self, service):
        user = make_user_data()
        prefs = PlanPreferences()

        profile = service.build_user_profile(user, prefs)

        assert profile.preferences["diet"] is None
        assert profile.preferences["allergies"] == []
        assert profile.preferences["cuisine_preferences"] == ["polish"]
        assert profile.preferences["excluded_ingredients"] == []
