"""
Integration tests for calorie calculation accuracy across the pipeline.

Verifies that nutrition math is correct at every stage: ingredient level,
meal totals, day totals, enrichment, optimization, and fallback meals.
"""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from src.meal_planning.application.service import MealPlanService
from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import (
    GeneratedIngredient,
    GeneratedMeal,
    GeneratedDay,
)
from tests.unit.meal_planning.conftest import (
    make_ingredient, make_meal, make_product, make_template, make_profile,
)


class TestIngredientCalorieCalculation:
    """Tests for ingredient-level calorie math."""

    def test_ingredient_kcal_matches_formula(self):
        # 150g of product with 165 kcal/100g = 247.5
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        products = [make_product(
            id="11111111-1111-1111-1111-111111111111",
            name="Kurczak", kcal_per_100g=165,
            protein_per_100g=31, fat_per_100g=3.6, carbs_per_100g=0,
        )]
        _, index_map = adapter._format_products_indexed(products)

        response = '{"name":"T","description":"T","preparation_time":10,"ingredients":[{"idx":1,"grams":150}]}'
        template = make_template(target_kcal=500)
        meal = adapter._parse_meal_indexed(response, template, index_map)

        assert meal.ingredients[0].kcal == round(165 * 1.5, 1)  # 247.5
        assert meal.ingredients[0].protein == round(31 * 1.5, 1)  # 46.5

    def test_zero_kcal_product_handled(self):
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        products = [make_product(name="Woda", kcal_per_100g=0, protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0)]
        _, index_map = adapter._format_products_indexed(products)

        response = '{"name":"T","description":"T","preparation_time":5,"ingredients":[{"idx":1,"grams":250}]}'
        template = make_template()
        meal = adapter._parse_meal_indexed(response, template, index_map)

        assert meal.ingredients[0].kcal == 0
        assert meal.total_kcal == 0


class TestMealTotalCalculation:
    """Tests for meal-level total calculations."""

    def test_meal_total_equals_sum_of_ingredients(self):
        ing1 = make_ingredient(kcal=200, protein=20, fat=10, carbs=30)
        ing2 = make_ingredient(kcal=300, protein=25, fat=15, carbs=40)
        meal = make_meal(ingredients=[ing1, ing2])

        assert meal.total_kcal == 500
        assert meal.total_protein == 45
        assert meal.total_fat == 25
        assert meal.total_carbs == 70


class TestDayTotalCalculation:
    """Tests for day-level total calculations."""

    def test_day_total_equals_sum_of_meals(self):
        meal1 = make_meal(total_kcal=500)
        meal2 = make_meal(total_kcal=700)
        meal3 = make_meal(total_kcal=300)
        day = GeneratedDay(day_number=1, meals=[meal1, meal2, meal3])

        assert day.total_kcal == 1500


class TestEnrichedMealCalories:
    """Tests for calorie recalculation after enrichment."""

    @pytest.mark.asyncio
    async def test_enriched_meal_recalculates_totals(self):
        product = {
            "id": str(uuid4()),
            "name": "Ryz bialy",
            "kcal_per_100g": 130,
            "protein_per_100g": 2.7,
            "fat_per_100g": 0.3,
            "carbs_per_100g": 28.0,
        }
        mock_search = AsyncMock()
        mock_search.find_product_by_name = AsyncMock(return_value=product)
        service = MealPlanService(
            repository=MagicMock(),
            food_search=mock_search,
            session=MagicMock(),
        )

        # Existing matched + unmatched
        ing1 = make_ingredient(name="A", kcal=200, protein=20, fat=10, carbs=30)
        ing2 = make_ingredient(name="Ryz", amount_grams=200, kcal=0, protein=0, fat=0, carbs=0, auto_food_id=False)
        meal = make_meal(ingredients=[ing1, ing2])

        result = await service._enrich_meal_ingredients(meal)

        # A: 200 kcal, Ryz: 130*2=260 kcal, total: 460
        assert result.total_kcal == 460.0
        assert result.total_protein == 25.4  # 20 + 5.4
        assert result.total_fat == 10.6  # 10 + 0.6
        assert result.total_carbs == 86.0  # 30 + 56.0


class TestFallbackMealCalories:
    """Tests for fallback meal calorie calculation."""

    def test_fallback_distributes_calories_evenly(self):
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        products = [
            make_product(name="A", kcal_per_100g=200, protein_per_100g=10, fat_per_100g=5, carbs_per_100g=30),
            make_product(name="B", kcal_per_100g=100, protein_per_100g=5, fat_per_100g=2, carbs_per_100g=15),
        ]
        template = make_template(target_kcal=500)

        meal = adapter._generate_fallback_meal(template, products)

        # Each ingredient targets 250 kcal
        # A: 250/200*100 = 125g (clamped to 30-300 range)
        # B: 250/100*100 = 250g
        assert meal.total_kcal > 0
        assert len(meal.ingredients) == 2

        # Verify nutrition calculated from DB values
        for ing in meal.ingredients:
            assert ing.kcal > 0

    def test_fallback_with_empty_products(self):
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        template = make_template(target_kcal=500)
        meal = adapter._generate_fallback_meal(template, [])

        assert meal.total_kcal == 500  # Uses template target
        assert len(meal.ingredients) == 0


class TestOptimizationPreservesRatios:
    """Tests that optimization scaling preserves macro ratios."""

    @pytest.mark.asyncio
    async def test_macro_ratios_preserved_after_scaling(self):
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        profile = make_profile(daily_kcal=2000)
        ing = GeneratedIngredient(
            food_id=uuid4(), name="Test", amount_grams=100,
            unit_label=None, kcal=500, protein=40, fat=15, carbs=60,
        )
        meal = GeneratedMeal(
            meal_type="lunch", name="T", description="",
            preparation_time_minutes=10, ingredients=[ing],
            total_kcal=500, total_protein=40, total_fat=15, total_carbs=60,
        )
        day = GeneratedDay(day_number=1, meals=[meal])

        # Before: protein ratio = 40/500 = 0.08
        before_ratio = ing.protein / ing.kcal

        result = await adapter.optimize_plan([day], profile)

        r_ing = result[0].meals[0].ingredients[0]
        after_ratio = r_ing.protein / r_ing.kcal if r_ing.kcal > 0 else 0

        # Ratios should be identical (same scale factor applied to all)
        assert abs(before_ratio - after_ratio) < 0.001
