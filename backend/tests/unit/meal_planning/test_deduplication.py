"""
Unit tests for meal template deduplication.

Tests _deduplicate_meal_templates to ensure repeated meals are detected and replaced.
"""
import pytest

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import MealTemplate
from tests.unit.meal_planning.conftest import make_profile, make_template


@pytest.fixture
def adapter():
    a = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
    a._model = None
    a._embedding_service = None
    return a


class TestDeduplicateMealTemplates:
    """Tests for _deduplicate_meal_templates."""

    def test_no_duplicates_returns_unchanged(self, adapter):
        """When no duplicates, templates should be unchanged."""
        profile = make_profile()
        templates = [
            [
                make_template(meal_type="breakfast", description="Owsianka"),
                make_template(meal_type="lunch", description="Kurczak z ryzem"),
            ],
            [
                make_template(meal_type="breakfast", description="Jajecznica"),
                make_template(meal_type="lunch", description="Zupa pomidorowa"),
            ],
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # Should be unchanged
        assert result[0][0].description == "Owsianka"
        assert result[0][1].description == "Kurczak z ryzem"
        assert result[1][0].description == "Jajecznica"
        assert result[1][1].description == "Zupa pomidorowa"

    def test_exact_duplicate_is_replaced(self, adapter):
        """Exact duplicate descriptions should be replaced."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="breakfast", description="Owsianka z bananem")],
            [make_template(meal_type="breakfast", description="Owsianka z bananem")],  # Duplicate
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # First should be unchanged, second should be replaced
        assert result[0][0].description == "Owsianka z bananem"
        assert result[1][0].description != "Owsianka z bananem"
        # Should have keywords
        assert result[1][0].ingredient_keywords

    def test_similar_descriptions_detected(self, adapter):
        """Similar descriptions (same first words) should be detected as duplicates."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="lunch", description="Kurczak z warzywami")],
            [make_template(meal_type="lunch", description="Kurczak z ryzem")],  # Similar
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # Second should be replaced because "Kurczak z" matches
        assert result[0][0].description == "Kurczak z warzywami"
        assert result[1][0].description != "Kurczak z ryzem"

    def test_case_insensitive_comparison(self, adapter):
        """Duplicate detection should be case-insensitive."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="dinner", description="Kanapki z serem")],
            [make_template(meal_type="dinner", description="kanapki z serem")],  # Same, different case
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # Second should be replaced
        assert result[1][0].description.lower() != "kanapki z serem"

    def test_different_meal_types_can_have_same_description(self, adapter):
        """Different meal types with same description should both be kept (but second replaced)."""
        profile = make_profile()
        templates = [
            [
                make_template(meal_type="breakfast", description="Jogurt z owocami"),
                make_template(meal_type="snack", description="Jogurt z owocami"),  # Same desc, diff type
            ],
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # First is kept, second is duplicate and replaced
        assert result[0][0].description == "Jogurt z owocami"
        assert result[0][1].description != "Jogurt z owocami"

    def test_replacement_has_correct_macros(self, adapter):
        """Replaced templates should keep original macro targets."""
        profile = make_profile()
        templates = [
            [make_template(
                meal_type="breakfast",
                description="Owsianka",
                target_kcal=500,
                target_protein=25.0,
            )],
            [make_template(
                meal_type="breakfast",
                description="Owsianka",  # Duplicate
                target_kcal=600,
                target_protein=30.0,
            )],
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # Second should have its original macros preserved
        assert result[1][0].target_kcal == 600
        assert result[1][0].target_protein == 30.0

    def test_multiple_duplicates_get_different_alternatives(self, adapter):
        """Multiple duplicates should get different alternatives."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="breakfast", description="Owsianka")],
            [make_template(meal_type="breakfast", description="Owsianka")],
            [make_template(meal_type="breakfast", description="Owsianka")],
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        descriptions = [day[0].description for day in result]

        # All three should be different
        assert len(set(descriptions)) == 3

    def test_handles_empty_templates(self, adapter):
        """Empty template list should be handled gracefully."""
        profile = make_profile()
        templates = []

        result = adapter._deduplicate_meal_templates(templates, profile)

        assert result == []

    def test_handles_empty_day(self, adapter):
        """Day with no templates should be handled gracefully."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="breakfast", description="Test")],
            [],  # Empty day
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        assert len(result) == 2
        assert result[0][0].description == "Test"
        assert result[1] == []

    def test_substring_match_detected(self, adapter):
        """Descriptions where one contains the other should be detected."""
        profile = make_profile()
        templates = [
            [make_template(meal_type="lunch", description="Zupa pomidorowa z makaronem")],
            [make_template(meal_type="lunch", description="Zupa pomidorowa")],  # Substring
        ]

        result = adapter._deduplicate_meal_templates(templates, profile)

        # Second should be replaced
        assert result[1][0].description != "Zupa pomidorowa"
