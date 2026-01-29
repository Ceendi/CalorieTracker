"""
Unit tests for indexed meal parser in BielikMealPlannerAdapter.

Tests the new Product-First Architecture where LLM selects products by index
instead of by name, ensuring 100% of ingredients are matched to database products.
"""

import pytest
from uuid import UUID

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import MealTemplate


@pytest.fixture
def adapter():
    """Create adapter instance (without loading the model)."""
    return BielikMealPlannerAdapter()


@pytest.fixture
def sample_template():
    """Sample meal template for testing."""
    return MealTemplate(
        meal_type="breakfast",
        target_kcal=500,
        target_protein=25.0,
        target_fat=15.0,
        target_carbs=60.0,
        description="Sniadanie owsiane",
    )


@pytest.fixture
def sample_products():
    """Sample products list as returned by RAG search."""
    return [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Platki owsiane",
            "category": "Zboza",
            "kcal_per_100g": 372,
            "protein_per_100g": 13.5,
            "fat_per_100g": 6.5,
            "carbs_per_100g": 58.0,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Mleko 2%",
            "category": "Nabial",
            "kcal_per_100g": 50,
            "protein_per_100g": 3.4,
            "fat_per_100g": 2.0,
            "carbs_per_100g": 4.8,
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "Banan",
            "category": "Owoce",
            "kcal_per_100g": 89,
            "protein_per_100g": 1.1,
            "fat_per_100g": 0.3,
            "carbs_per_100g": 22.8,
        },
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "name": "Miod naturalny",
            "category": "Slodziki",
            "kcal_per_100g": 304,
            "protein_per_100g": 0.3,
            "fat_per_100g": 0.0,
            "carbs_per_100g": 82.0,
        },
    ]


class TestFormatProductsIndexed:
    """Tests for _format_products_indexed method."""

    def test_formats_products_with_indices(self, adapter, sample_products):
        """Products should be formatted with sequential indices."""
        text, index_map = adapter._format_products_indexed(sample_products)

        assert "[1] Platki owsiane" in text
        assert "[2] Mleko 2%" in text
        assert "[3] Banan" in text
        assert "[4] Miod naturalny" in text

    def test_includes_nutrition_info(self, adapter, sample_products):
        """Each product line should include kcal and macros."""
        text, _ = adapter._format_products_indexed(sample_products)

        # Check first product has nutrition
        assert "372 kcal" in text
        assert "B:14g" in text or "B:13g" in text  # Rounded
        assert "T:7g" in text or "T:6g" in text
        assert "W:58g" in text

    def test_returns_correct_index_map(self, adapter, sample_products):
        """Index map should map indices to original products."""
        _, index_map = adapter._format_products_indexed(sample_products)

        assert len(index_map) == 4
        assert index_map[1]["name"] == "Platki owsiane"
        assert index_map[2]["name"] == "Mleko 2%"
        assert index_map[3]["name"] == "Banan"
        assert index_map[4]["name"] == "Miod naturalny"

    def test_empty_products_returns_empty(self, adapter):
        """Empty products list should return empty string and map."""
        text, index_map = adapter._format_products_indexed([])

        assert text == ""
        assert index_map == {}


class TestParseMealIndexed:
    """Tests for _parse_meal_indexed method."""

    def test_parses_valid_indexed_response(self, adapter, sample_template, sample_products):
        """Should correctly parse LLM response with idx format."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Owsianka z bananem", "description": "Zdrowe sniadanie",
        "preparation_time": 10, "ingredients": [
            {"idx": 1, "grams": 80},
            {"idx": 2, "grams": 200},
            {"idx": 3, "grams": 100}
        ]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        assert meal.name == "Owsianka z bananem"
        assert meal.description == "Zdrowe sniadanie"
        assert len(meal.ingredients) == 3

        # Check ingredients have correct food_id and names from DB
        assert meal.ingredients[0].name == "Platki owsiane"
        assert meal.ingredients[0].food_id == UUID("11111111-1111-1111-1111-111111111111")
        assert meal.ingredients[0].amount_grams == 80.0

        assert meal.ingredients[1].name == "Mleko 2%"
        assert meal.ingredients[2].name == "Banan"

    def test_calculates_nutrition_from_database(self, adapter, sample_template, sample_products):
        """Nutrition should be calculated from database values, not estimates."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test",
        "preparation_time": 5, "ingredients": [{"idx": 1, "grams": 100}]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        # 100g of platki owsiane = 372 kcal
        assert meal.ingredients[0].kcal == 372.0
        assert meal.ingredients[0].protein == 13.5
        assert meal.total_kcal == 372.0

    def test_skips_invalid_indices(self, adapter, sample_template, sample_products):
        """Should skip ingredients with invalid indices."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test", "preparation_time": 5,
        "ingredients": [
            {"idx": 1, "grams": 100},
            {"idx": 99, "grams": 50},
            {"idx": 2, "grams": 150}
        ]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        # Only 2 valid ingredients (idx 1 and 2)
        assert len(meal.ingredients) == 2
        assert meal.ingredients[0].name == "Platki owsiane"
        assert meal.ingredients[1].name == "Mleko 2%"

    def test_handles_string_grams(self, adapter, sample_template, sample_products):
        """Should handle grams specified as strings."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test", "preparation_time": 5,
        "ingredients": [{"idx": 1, "grams": "150g"}]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        assert meal.ingredients[0].amount_grams == 150.0

    def test_clamps_extreme_grams(self, adapter, sample_template, sample_products):
        """Should clamp grams to reasonable range (5-1000g)."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test", "preparation_time": 5,
        "ingredients": [
            {"idx": 1, "grams": 1},
            {"idx": 2, "grams": 5000}
        ]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        assert meal.ingredients[0].amount_grams == 5.0  # Clamped up
        assert meal.ingredients[1].amount_grams == 1000.0  # Clamped down

    def test_supports_alternative_field_names(self, adapter, sample_template, sample_products):
        """Should support 'index' instead of 'idx' and 'amount' instead of 'grams'."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test", "preparation_time": 5,
        "ingredients": [{"index": 1, "amount": 100}]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        assert len(meal.ingredients) == 1
        assert meal.ingredients[0].amount_grams == 100.0

    def test_returns_fallback_on_empty_ingredients(self, adapter, sample_template, sample_products):
        """Should return fallback meal if all indices are invalid."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = '''{"name": "Test", "description": "Test", "preparation_time": 5,
        "ingredients": [{"idx": 99, "grams": 100}]}'''

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        # Fallback meal should have real ingredients
        assert len(meal.ingredients) > 0
        assert meal.ingredients[0].food_id is not None

    def test_returns_fallback_on_invalid_json(self, adapter, sample_template, sample_products):
        """Should return fallback meal if JSON parsing fails."""
        _, index_map = adapter._format_products_indexed(sample_products)

        response = "Not valid JSON at all"

        meal = adapter._parse_meal_indexed(response, sample_template, index_map)

        assert meal.meal_type == sample_template.meal_type
        assert len(meal.ingredients) > 0  # Fallback has real ingredients


class TestGenerateFallbackMeal:
    """Tests for _generate_fallback_meal method."""

    def test_uses_available_products(self, adapter, sample_template, sample_products):
        """Fallback should use products from the available list."""
        meal = adapter._generate_fallback_meal(sample_template, sample_products)

        assert len(meal.ingredients) > 0
        # All ingredients should have food_id
        for ing in meal.ingredients:
            assert ing.food_id is not None

    def test_calculates_grams_to_hit_target(self, adapter, sample_template, sample_products):
        """Fallback should calculate grams to approximate target calories."""
        meal = adapter._generate_fallback_meal(sample_template, sample_products)

        # Total kcal should be somewhat close to target (not exactly, but reasonable)
        assert meal.total_kcal > 0
        # Within 50% of target is acceptable for fallback
        assert 0.5 * sample_template.target_kcal <= meal.total_kcal <= 2.0 * sample_template.target_kcal

    def test_handles_empty_products_list(self, adapter, sample_template):
        """Should handle empty products list gracefully."""
        meal = adapter._generate_fallback_meal(sample_template, [])

        assert meal.meal_type == sample_template.meal_type
        assert len(meal.ingredients) == 0
        # Uses template targets for stats
        assert meal.total_kcal == sample_template.target_kcal

    def test_handles_none_products(self, adapter, sample_template):
        """Should handle None products list gracefully."""
        meal = adapter._generate_fallback_meal(sample_template, None)

        assert meal.meal_type == sample_template.meal_type
        assert len(meal.ingredients) == 0

    def test_uses_product_names_from_database(self, adapter, sample_template, sample_products):
        """Ingredient names should come from database, not hallucinated."""
        meal = adapter._generate_fallback_meal(sample_template, sample_products)

        valid_names = {p["name"] for p in sample_products}
        for ing in meal.ingredients:
            assert ing.name in valid_names
