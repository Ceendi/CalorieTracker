"""
Unit tests for BielikMealPlannerAdapter helper methods.

Tests _format_preferences, _extract_json, _clean_json, _parse_templates,
_generate_default_templates, and _generate_default_day_templates.
"""
import json
import pytest

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from tests.unit.meal_planning.conftest import make_profile


@pytest.fixture
def adapter():
    a = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
    a._model = None
    a._embedding_service = None
    return a


# ---------------------------------------------------------------------------
# _format_preferences
# ---------------------------------------------------------------------------

class TestFormatPreferences:
    """Tests for _format_preferences."""

    def test_vegetarian_translated_to_polish(self, adapter):
        result = adapter._format_preferences({"diet": "vegetarian"})
        assert "WEGETARIANSKA" in result
        assert result.startswith("DIETA:")

    def test_vegan_translated_to_polish(self, adapter):
        result = adapter._format_preferences({"diet": "vegan"})
        assert "WEGANSKA" in result

    def test_keto_translated_to_polish(self, adapter):
        result = adapter._format_preferences({"diet": "keto"})
        assert "KETOGENICZNA" in result

    def test_low_gi_translated_to_polish(self, adapter):
        result = adapter._format_preferences({"diet": "low_gi"})
        assert "NISKOINDEKSOWA GLIKEMICZNIE" in result

    def test_unknown_diet_used_as_is(self, adapter):
        result = adapter._format_preferences({"diet": "paleo"})
        assert "PALEO" in result

    def test_allergies_formatted(self, adapter):
        result = adapter._format_preferences({"allergies": ["gluten", "laktoza"]})
        assert "ALERGIA NA:" in result
        assert "GLUTEN" in result
        assert "LAKTOZA" in result

    def test_cuisine_preferences_formatted(self, adapter):
        result = adapter._format_preferences({"cuisine_preferences": ["polska", "wloska"]})
        assert "PREFEROWANA KUCHNIA:" in result
        assert "POLSKA" in result
        assert "WLOSKA" in result

    def test_excluded_ingredients_formatted(self, adapter):
        result = adapter._format_preferences({"excluded_ingredients": ["cukier", "sol"]})
        assert "WYKLUCZONE SKLADNIKI:" in result
        assert "CUKIER" in result
        assert "SOL" in result

    def test_empty_preferences_returns_default(self, adapter):
        result = adapter._format_preferences({})
        assert "BRAK SZCZEGOLNYCH WYMAGAN" in result

    def test_multiple_preferences_combined(self, adapter):
        result = adapter._format_preferences({
            "diet": "vegan",
            "allergies": ["gluten"],
            "excluded_ingredients": ["cukier"],
        })
        assert "WEGANSKA" in result
        assert "GLUTEN" in result
        assert "CUKIER" in result

    def test_none_values_ignored(self, adapter):
        result = adapter._format_preferences({"diet": None, "allergies": []})
        assert "BRAK SZCZEGOLNYCH WYMAGAN" in result


# ---------------------------------------------------------------------------
# _extract_json
# ---------------------------------------------------------------------------

class TestExtractJson:
    """Tests for _extract_json."""

    def test_extracts_from_code_block(self, adapter):
        text = '```json\n{"key": "value"}\n```'
        result = adapter._extract_json(text)
        assert json.loads(result) == {"key": "value"}

    def test_extracts_raw_json(self, adapter):
        text = 'Some text before {"key": "value"} some after'
        result = adapter._extract_json(text)
        assert json.loads(result) == {"key": "value"}

    def test_extracts_nested_json(self, adapter):
        text = '{"outer": {"inner": "value"}}'
        result = adapter._extract_json(text)
        data = json.loads(result)
        assert data["outer"]["inner"] == "value"

    def test_handles_json_with_arrays(self, adapter):
        text = '{"items": [1, 2, 3]}'
        result = adapter._extract_json(text)
        data = json.loads(result)
        assert data["items"] == [1, 2, 3]

    def test_raises_value_error_no_opening_brace(self, adapter):
        with pytest.raises(ValueError):
            adapter._extract_json("no json here")

    def test_handles_trailing_text_after_json(self, adapter):
        text = '{"key": "val"}\n\nsome garbage text'
        result = adapter._extract_json(text)
        assert json.loads(result) == {"key": "val"}

    def test_code_block_without_json_label(self, adapter):
        text = '```\n{"key": "value"}\n```'
        result = adapter._extract_json(text)
        assert json.loads(result) == {"key": "value"}


# ---------------------------------------------------------------------------
# _clean_json
# ---------------------------------------------------------------------------

class TestCleanJson:
    """Tests for _clean_json."""

    def test_removes_single_line_comments(self, adapter):
        raw = '{"key": "value" // comment\n}'
        result = adapter._clean_json(raw)
        data = json.loads(result)
        assert data["key"] == "value"

    def test_removes_trailing_comma_before_closing_brace(self, adapter):
        raw = '{"a": 1,}'
        result = adapter._clean_json(raw)
        data = json.loads(result)
        assert data["a"] == 1

    def test_removes_trailing_comma_before_closing_bracket(self, adapter):
        raw = '{"a": [1, 2,]}'
        result = adapter._clean_json(raw)
        data = json.loads(result)
        assert data["a"] == [1, 2]

    def test_preserves_valid_json(self, adapter):
        raw = '{"a": 1}'
        result = adapter._clean_json(raw)
        assert json.loads(result) == {"a": 1}


# ---------------------------------------------------------------------------
# _parse_templates
# ---------------------------------------------------------------------------

class TestParseTemplates:
    """Tests for _parse_templates."""

    def test_parses_valid_template_json(self, adapter):
        profile = make_profile(daily_kcal=2000, daily_protein=150, daily_fat=55, daily_carbs=225)
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [
                    {"type": "breakfast", "description": "Owsianka"},
                    {"type": "lunch", "description": "Kurczak z ryzem"},
                ]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)

        assert len(templates) == 1
        # Implementation auto-fills missing meal types to ensure complete daily plans
        assert len(templates[0]) == 5
        
        # Find the breakfast and lunch meals (order may vary due to auto-fill)
        meals_by_type = {t.meal_type: t for t in templates[0]}
        
        assert "breakfast" in meals_by_type
        assert meals_by_type["breakfast"].description == "Owsianka"
        
        assert "lunch" in meals_by_type
        assert meals_by_type["lunch"].description == "Kurczak z ryzem"
        
        # Verify missing meals were auto-filled with specific default descriptions
        assert "second_breakfast" in meals_by_type
        assert meals_by_type["second_breakfast"].description == "Jogurt z orzechami"
        assert meals_by_type["second_breakfast"].ingredient_keywords  # Should have keywords

        assert "snack" in meals_by_type
        assert meals_by_type["snack"].description == "Owoce z orzechami"
        assert meals_by_type["snack"].ingredient_keywords  # Should have keywords

        assert "dinner" in meals_by_type
        assert meals_by_type["dinner"].description == "Kanapki z serem i warzywami"
        assert meals_by_type["dinner"].ingredient_keywords  # Should have keywords

    def test_calculates_macros_from_profile_ratios(self, adapter):
        profile = make_profile(daily_kcal=2000, daily_protein=150, daily_fat=55, daily_carbs=225)
        response = json.dumps({
            "days": [{"day": 1, "meals": [{"type": "breakfast", "description": "Test"}]}]
        })

        templates = adapter._parse_templates(response, profile, 1)

        # breakfast ratio = 0.25
        assert templates[0][0].target_kcal == int(2000 * 0.25)  # 500
        assert templates[0][0].target_protein == round(150 * 0.25, 1)

    def test_pads_with_defaults_when_fewer_days(self, adapter):
        profile = make_profile()
        response = json.dumps({
            "days": [{"day": 1, "meals": [{"type": "breakfast", "description": "Test"}]}]
        })

        templates = adapter._parse_templates(response, profile, 3)

        assert len(templates) == 3  # Padded to 3

    def test_truncates_extra_days(self, adapter):
        profile = make_profile()
        days_data = [{"day": i, "meals": [{"type": "breakfast", "description": "Test"}]} for i in range(10)]
        response = json.dumps({"days": days_data})

        templates = adapter._parse_templates(response, profile, 3)

        assert len(templates) == 3

    def test_falls_back_on_invalid_json(self, adapter):
        profile = make_profile()

        templates = adapter._parse_templates("not json at all", profile, 2)

        assert len(templates) == 2
        assert len(templates[0]) == 5  # Default: 5 meals per day

    def test_unknown_meal_type_gets_default_ratio(self, adapter):
        profile = make_profile(daily_kcal=2000)
        response = json.dumps({
            "days": [{"day": 1, "meals": [{"type": "brunch", "description": "Test"}]}]
        })

        templates = adapter._parse_templates(response, profile, 1)

        # Unknown type defaults to 0.20 ratio
        assert templates[0][0].target_kcal == int(2000 * 0.20)


# ---------------------------------------------------------------------------
# _generate_default_templates
# ---------------------------------------------------------------------------

class TestGenerateDefaultTemplates:
    """Tests for _generate_default_templates."""

    def test_generates_correct_number_of_days(self, adapter):
        profile = make_profile()
        templates = adapter._generate_default_templates(profile, 7)
        assert len(templates) == 7

    def test_each_day_has_five_meals(self, adapter):
        profile = make_profile()
        templates = adapter._generate_default_templates(profile, 1)
        assert len(templates[0]) == 5

    def test_meal_types_correct(self, adapter):
        profile = make_profile()
        templates = adapter._generate_default_templates(profile, 1)
        types = [t.meal_type for t in templates[0]]
        assert "breakfast" in types
        assert "second_breakfast" in types
        assert "lunch" in types
        assert "snack" in types
        assert "dinner" in types

    def test_target_kcal_sums_approximately_to_daily(self, adapter):
        profile = make_profile(daily_kcal=2000)
        templates = adapter._generate_default_templates(profile, 1)
        total = sum(t.target_kcal for t in templates[0])
        # Distribution: 0.25 + 0.10 + 0.35 + 0.10 + 0.20 = 1.0
        # int() truncation may lose up to 4 kcal total
        assert abs(total - 2000) <= 5
