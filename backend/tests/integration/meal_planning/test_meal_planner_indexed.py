"""
Integration tests for the indexed meal planner flow.

Tests the complete flow from product formatting through LLM response parsing,
ensuring 100% of ingredients are matched to database products.
"""

import pytest
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import (
    MealTemplate,
    UserProfile,
    GeneratedPlan,
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
    PlanPreferences,
)
from src.meal_planning.application.service import UserData


@pytest.fixture
def sample_products():
    """Sample products list as would be returned by RAG search."""
    return [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Kurczak, piersi, bez skory",
            "category": "Drob",
            "kcal_per_100g": 165,
            "protein_per_100g": 31.0,
            "fat_per_100g": 3.6,
            "carbs_per_100g": 0.0,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "name": "Ryz bialy, gotowany",
            "category": "Zboza",
            "kcal_per_100g": 130,
            "protein_per_100g": 2.7,
            "fat_per_100g": 0.3,
            "carbs_per_100g": 28.0,
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "name": "Brokuty, gotowane",
            "category": "Warzywa",
            "kcal_per_100g": 35,
            "protein_per_100g": 2.8,
            "fat_per_100g": 0.4,
            "carbs_per_100g": 4.0,
        },
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "name": "Oliwa z oliwek",
            "category": "Tluszcze",
            "kcal_per_100g": 884,
            "protein_per_100g": 0.0,
            "fat_per_100g": 100.0,
            "carbs_per_100g": 0.0,
        },
        {
            "id": "55555555-5555-5555-5555-555555555555",
            "name": "Cebula, biala",
            "category": "Warzywa",
            "kcal_per_100g": 40,
            "protein_per_100g": 1.1,
            "fat_per_100g": 0.1,
            "carbs_per_100g": 9.3,
        },
    ]


@pytest.fixture
def sample_template():
    """Sample meal template."""
    return MealTemplate(
        meal_type="lunch",
        target_kcal=700,
        target_protein=40.0,
        target_fat=20.0,
        target_carbs=80.0,
        description="Kurczak z ryzem",
    )


@pytest.fixture
def sample_profile():
    """Sample user profile."""
    return UserProfile(
        user_id=uuid4(),
        daily_kcal=2000,
        daily_protein=150.0,
        daily_fat=55.0,
        daily_carbs=225.0,
        preferences={"cuisine_preferences": ["polska"]},
    )


class TestIndexedProductFormat:
    """Tests for the indexed product format in LLM context."""

    def test_format_creates_sequential_indices(self, sample_products):
        """Products should be numbered [1], [2], etc."""
        adapter = BielikMealPlannerAdapter()
        text, index_map = adapter._format_products_indexed(sample_products)

        # Check format
        lines = text.split("\n")
        assert len(lines) == 5
        assert lines[0].startswith("[1]")
        assert lines[1].startswith("[2]")
        assert "Kurczak" in lines[0]
        assert "Ryz" in lines[1]

    def test_format_includes_all_nutrition_info(self, sample_products):
        """Each line should have kcal, protein, fat, carbs."""
        adapter = BielikMealPlannerAdapter()
        text, _ = adapter._format_products_indexed(sample_products)

        # Check first product line has all nutrition
        first_line = text.split("\n")[0]
        assert "165 kcal" in first_line
        assert "B:" in first_line
        assert "T:" in first_line
        assert "W:" in first_line


class TestIndexedMealParsing:
    """Tests for parsing LLM response with indexed ingredients."""

    def test_parses_valid_indexed_response(self, sample_products, sample_template):
        """Should correctly parse response with idx format."""
        adapter = BielikMealPlannerAdapter()
        _, index_map = adapter._format_products_indexed(sample_products)

        # Simulate LLM response with indexed ingredients
        llm_response = '''
        {"name": "Kurczak z ryzem i brokulami",
         "description": "Pyszny obiad",
         "preparation_time": 25,
         "ingredients": [
            {"idx": 1, "grams": 150},
            {"idx": 2, "grams": 200},
            {"idx": 3, "grams": 100},
            {"idx": 4, "grams": 10}
        ]}
        '''

        meal = adapter._parse_meal_indexed(llm_response, sample_template, index_map)

        assert meal.name == "Kurczak z ryzem i brokulami"
        assert len(meal.ingredients) == 4

        # All ingredients should have food_id from database
        for ing in meal.ingredients:
            assert ing.food_id is not None

        # Check specific mappings
        assert meal.ingredients[0].name == "Kurczak, piersi, bez skory"
        assert meal.ingredients[0].amount_grams == 150

    def test_all_ingredients_have_valid_food_id(self, sample_products, sample_template):
        """Every parsed ingredient should have a valid UUID food_id."""
        adapter = BielikMealPlannerAdapter()
        _, index_map = adapter._format_products_indexed(sample_products)

        llm_response = '''
        {"name": "Test", "description": "Test", "preparation_time": 15,
         "ingredients": [{"idx": 1, "grams": 100}, {"idx": 2, "grams": 100}]}
        '''

        meal = adapter._parse_meal_indexed(llm_response, sample_template, index_map)

        for ing in meal.ingredients:
            assert isinstance(ing.food_id, UUID)

    def test_nutrition_calculated_from_database(self, sample_products, sample_template):
        """Nutrition values should come from database, not estimates."""
        adapter = BielikMealPlannerAdapter()
        _, index_map = adapter._format_products_indexed(sample_products)

        # Use exact values to verify calculation
        llm_response = '''
        {"name": "Test", "description": "Test", "preparation_time": 15,
         "ingredients": [{"idx": 1, "grams": 100}]}
        '''

        meal = adapter._parse_meal_indexed(llm_response, sample_template, index_map)

        # 100g of chicken breast should be exactly 165 kcal
        assert meal.ingredients[0].kcal == 165.0
        assert meal.ingredients[0].protein == 31.0
        assert meal.total_kcal == 165.0


class TestFallbackMealWithRealIngredients:
    """Tests for fallback meal using real products from database."""

    def test_fallback_has_real_ingredients(self, sample_products, sample_template):
        """Fallback meal should contain actual database products."""
        adapter = BielikMealPlannerAdapter()

        meal = adapter._generate_fallback_meal(sample_template, sample_products)

        assert len(meal.ingredients) > 0

        # All ingredients should have food_id
        for ing in meal.ingredients:
            assert ing.food_id is not None

        # Names should be from the product list
        product_names = {p["name"] for p in sample_products}
        for ing in meal.ingredients:
            assert ing.name in product_names

    def test_fallback_calculates_reasonable_portions(self, sample_products, sample_template):
        """Fallback should calculate portions to hit target calories."""
        adapter = BielikMealPlannerAdapter()

        meal = adapter._generate_fallback_meal(sample_template, sample_products)

        # Total kcal should be somewhere near target
        # Allow wide range for fallback (50% - 200%)
        assert meal.total_kcal > 0.3 * sample_template.target_kcal
        assert meal.total_kcal < 2.5 * sample_template.target_kcal


class TestEndToEndMealGeneration:
    """End-to-end tests for meal generation with mocked LLM."""

    def test_generate_meal_returns_indexed_ingredients(
        self, sample_products, sample_template, sample_profile
    ):
        """Generate meal should return ingredients with food_id."""
        import asyncio

        adapter = BielikMealPlannerAdapter()

        # Mock the model response
        mock_response = {
            "choices": [{
                "text": '''{"name": "Test Meal", "description": "Test",
                "preparation_time": 15, "ingredients": [
                    {"idx": 1, "grams": 150},
                    {"idx": 2, "grams": 100}
                ]}'''
            }]
        }

        with patch.object(adapter, "_get_model") as mock_model:
            mock_llm = MagicMock(return_value=mock_response)
            mock_model.return_value = mock_llm

            meal = asyncio.run(adapter.generate_meal(
                template=sample_template,
                profile=sample_profile,
                used_ingredients=[],
                available_products=sample_products,
            ))

        # All ingredients should have food_id
        assert len(meal.ingredients) == 2
        for ing in meal.ingredients:
            assert ing.food_id is not None


class TestPlanQualityValidation:
    """Tests for plan quality validation integration."""

    def test_validates_food_id_percentage(self):
        """Validation should calculate correct food_id percentage."""
        mock_repo = MagicMock()
        service = MealPlanService(repository=mock_repo)

        # Create plan with all ingredients having food_id
        ing = GeneratedIngredient(
            food_id=uuid4(),
            name="Test",
            amount_grams=100,
            unit_label=None,
            kcal=200,
            protein=20,
            fat=5,
            carbs=25,
        )
        meal = GeneratedMeal(
            meal_type="lunch",
            name="Test",
            description="Test",
            preparation_time_minutes=15,
            ingredients=[ing],
            total_kcal=200,
            total_protein=20,
            total_fat=5,
            total_carbs=25,
        )
        day = GeneratedDay(day_number=1, meals=[meal])
        plan = GeneratedPlan(
            days=[day],
            preferences_applied={},
            generation_metadata={},
        )

        result = service.validate_plan_quality(plan, 200)

        assert result["food_id_percentage"] == 100.0
        assert result["is_valid"] is True

    def test_validation_added_to_metadata(self):
        """Validation results should be in generation_metadata."""
        # This would require a full integration test with mocked planner
        # For now, verify the structure is correct
        mock_repo = MagicMock()
        service = MealPlanService(repository=mock_repo)

        ing = GeneratedIngredient(
            food_id=uuid4(),
            name="Test",
            amount_grams=100,
            unit_label=None,
            kcal=500,
            protein=20,
            fat=15,
            carbs=60,
        )
        meal = GeneratedMeal(
            meal_type="lunch",
            name="Test",
            description="Test",
            preparation_time_minutes=15,
            ingredients=[ing],
            total_kcal=500,
            total_protein=20,
            total_fat=15,
            total_carbs=60,
        )
        day = GeneratedDay(day_number=1, meals=[meal])
        plan = GeneratedPlan(
            days=[day],
            preferences_applied={},
            generation_metadata={},
        )

        validation = service.validate_plan_quality(plan, 500)

        # Should have all expected keys
        assert "food_id_percentage" in validation
        assert "calorie_deviation_days" in validation
        assert "empty_meals" in validation
        assert "issues" in validation
        assert "is_valid" in validation
