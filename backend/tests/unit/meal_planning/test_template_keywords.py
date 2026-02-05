"""
Unit tests for ingredient keyword extraction and parsing in meal templates.

Tests _extract_keywords_from_description and keyword parsing in _parse_templates.
"""
import json
import pytest

from src.meal_planning.adapters.bielik_meal_planner import (
    BielikMealPlannerAdapter,
    DISH_TO_INGREDIENTS,
)
from tests.unit.meal_planning.conftest import make_profile


@pytest.fixture
def adapter():
    a = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
    a._model = None
    a._embedding_service = None
    return a


# ---------------------------------------------------------------------------
# _extract_keywords_from_description
# ---------------------------------------------------------------------------

class TestExtractKeywordsFromDescription:
    """Tests for _extract_keywords_from_description."""

    def test_extracts_known_dish_ingredients(self, adapter):
        """Known dish stems should map to their ingredients."""
        keywords = adapter._extract_keywords_from_description("Kanapki z serem")
        # "kanapk" stem should map to ["chleb", "pieczywo"]
        assert "chleb" in keywords or "pieczywo" in keywords

    def test_extracts_jajecznica_as_jajko(self, adapter):
        """Jajecznica should extract jajko."""
        keywords = adapter._extract_keywords_from_description("Jajecznica z warzywami")
        assert "jajko" in keywords

    def test_extracts_owsianka_as_platki(self, adapter):
        """Owsianka should extract platki owsiane."""
        keywords = adapter._extract_keywords_from_description("Owsianka z bananem")
        assert any("platki" in k or "owsiane" in k or "owsianka" in k for k in keywords)

    def test_extracts_additional_words_from_description(self, adapter):
        """Words in description that are not dish stems should be extracted."""
        keywords = adapter._extract_keywords_from_description("Kanapki z twarogiem i rzodkiewka")
        # Should have chleb/pieczywo from kanapki + twarogiem + rzodkiewka
        assert any("twarog" in k for k in keywords)
        assert any("rzodkiew" in k for k in keywords)

    def test_filters_stop_words(self, adapter):
        """Polish stop words should be filtered out."""
        keywords = adapter._extract_keywords_from_description("Owsianka z bananem i mlekiem")
        assert "z" not in keywords
        assert "i" not in keywords

    def test_returns_empty_for_empty_description(self, adapter):
        """Empty description should return empty list."""
        keywords = adapter._extract_keywords_from_description("")
        assert keywords == []

    def test_returns_empty_for_none_description(self, adapter):
        """None description should return empty list."""
        keywords = adapter._extract_keywords_from_description(None)
        assert keywords == []

    def test_limits_to_5_keywords(self, adapter):
        """Should return at most 5 keywords."""
        # Long description with many potential keywords
        keywords = adapter._extract_keywords_from_description(
            "Kanapki z serem, szynka, pomidorem, ogorkiem, salata, maslem i cebula"
        )
        assert len(keywords) <= 5

    def test_handles_zupa_dish(self, adapter):
        """Zupa should extract bulion/warzywa."""
        keywords = adapter._extract_keywords_from_description("Zupa pomidorowa")
        # Should have something related to zupa
        assert any("bulion" in k or "warzywa" in k or "pomidor" in k for k in keywords)

    def test_deduplicates_keywords(self, adapter):
        """Should not have exact duplicate keywords."""
        keywords = adapter._extract_keywords_from_description("Owsianka z bananem i bananem")
        # Same word repeated should appear only once
        banan_count = sum(1 for k in keywords if k == "bananem")
        assert banan_count <= 1  # Should be deduplicated


# ---------------------------------------------------------------------------
# _parse_templates with keywords
# ---------------------------------------------------------------------------

class TestParseTemplatesWithKeywords:
    """Tests for _parse_templates keyword extraction."""

    def test_extracts_keywords_from_llm_response(self, adapter):
        """Keywords from LLM response should be extracted."""
        profile = make_profile(daily_kcal=2000, daily_protein=150, daily_fat=55, daily_carbs=225)
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "breakfast",
                    "description": "Owsianka z bananem",
                    "keywords": ["platki owsiane", "banan", "mleko"]
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)

        # Find breakfast template
        breakfast = next(t for t in templates[0] if t.meal_type == "breakfast")
        assert breakfast.ingredient_keywords == ["platki owsiane", "banan", "mleko"]

    def test_normalizes_keywords_to_lowercase(self, adapter):
        """Keywords should be normalized to lowercase."""
        profile = make_profile()
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "breakfast",
                    "description": "Test",
                    "keywords": ["CHLEB", "Maslo", "SER"]
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)
        breakfast = next(t for t in templates[0] if t.meal_type == "breakfast")

        assert all(k.islower() for k in breakfast.ingredient_keywords)
        assert "chleb" in breakfast.ingredient_keywords
        assert "maslo" in breakfast.ingredient_keywords
        assert "ser" in breakfast.ingredient_keywords

    def test_strips_whitespace_from_keywords(self, adapter):
        """Keywords should have whitespace stripped."""
        profile = make_profile()
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "breakfast",
                    "description": "Test",
                    "keywords": [" chleb ", "maslo  ", "  ser"]
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)
        breakfast = next(t for t in templates[0] if t.meal_type == "breakfast")

        assert "chleb" in breakfast.ingredient_keywords
        assert "maslo" in breakfast.ingredient_keywords
        assert "ser" in breakfast.ingredient_keywords

    def test_falls_back_to_extraction_when_no_keywords(self, adapter):
        """When LLM doesn't provide keywords, should extract from description."""
        profile = make_profile()
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "dinner",
                    "description": "Kanapki z twarogiem i rzodkiewka"
                    # No keywords field
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)
        dinner = next(t for t in templates[0] if t.meal_type == "dinner")

        # Should have extracted keywords from description
        assert len(dinner.ingredient_keywords) > 0
        # Should include chleb from kanapki mapping
        assert any("chleb" in k or "pieczywo" in k for k in dinner.ingredient_keywords)

    def test_falls_back_when_keywords_empty_list(self, adapter):
        """When keywords is empty list, should extract from description."""
        profile = make_profile()
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "breakfast",
                    "description": "Jajecznica z warzywami",
                    "keywords": []  # Empty list
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)
        breakfast = next(t for t in templates[0] if t.meal_type == "breakfast")

        # Should have extracted keywords from description
        assert len(breakfast.ingredient_keywords) > 0
        assert any("jajko" in k for k in breakfast.ingredient_keywords)

    def test_filters_non_string_keywords(self, adapter):
        """Non-string values in keywords list should be filtered out."""
        profile = make_profile()
        response = json.dumps({
            "days": [{
                "day": 1,
                "meals": [{
                    "type": "breakfast",
                    "description": "Test",
                    "keywords": ["chleb", 123, None, "maslo", {"nested": "obj"}]
                }]
            }]
        })

        templates = adapter._parse_templates(response, profile, 1)
        breakfast = next(t for t in templates[0] if t.meal_type == "breakfast")

        # Only string keywords should remain
        assert breakfast.ingredient_keywords == ["chleb", "maslo"]

    def test_default_templates_have_keywords(self, adapter):
        """Default templates (fallback) should have ingredient keywords for product search."""
        profile = make_profile()
        templates = adapter._generate_default_templates(profile, 1)

        # All default templates should have keywords to enable proper product search
        for template in templates[0]:
            assert template.ingredient_keywords, (
                f"Default template '{template.meal_type}' should have keywords"
            )
            assert len(template.ingredient_keywords) >= 2, (
                f"Default template '{template.meal_type}' should have at least 2 keywords"
            )


# ---------------------------------------------------------------------------
# DISH_TO_INGREDIENTS mapping sanity checks
# ---------------------------------------------------------------------------

class TestDishToIngredientsMapping:
    """Tests for the DISH_TO_INGREDIENTS dictionary."""

    def test_kanapk_maps_to_bread(self):
        """Kanapk stem should map to bread."""
        assert "kanapk" in DISH_TO_INGREDIENTS
        ingredients = DISH_TO_INGREDIENTS["kanapk"]
        assert "chleb" in ingredients or "pieczywo" in ingredients

    def test_jajecznic_maps_to_egg(self):
        """Jajecznic stem should map to egg."""
        assert "jajecznic" in DISH_TO_INGREDIENTS
        assert "jajko" in DISH_TO_INGREDIENTS["jajecznic"]

    def test_owsiank_maps_to_oats(self):
        """Owsiank stem should map to oats."""
        assert "owsiank" in DISH_TO_INGREDIENTS
        ingredients = DISH_TO_INGREDIENTS["owsiank"]
        assert any("platki" in i or "owsian" in i for i in ingredients)
