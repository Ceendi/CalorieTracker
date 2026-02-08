import pytest
import uuid
from src.food_catalogue.domain.entities import Food, Nutrition, UnitInfo

def test_nutrition_creation():
    nutrition = Nutrition(
        kcal_per_100g=100.0,
        protein_per_100g=10.0,
        fat_per_100g=5.0,
        carbs_per_100g=20.0
    )
    assert nutrition.kcal_per_100g == 100.0
    assert nutrition.protein_per_100g == 10.0
    assert nutrition.fat_per_100g == 5.0
    assert nutrition.carbs_per_100g == 20.0

def test_unit_info_creation():
    unit = UnitInfo(unit="glass", grams=200.0, label="1 glass (200g)")
    assert unit.unit == "glass"
    assert unit.grams == 200.0
    assert unit.label == "1 glass (200g)"

def test_food_creation():
    nutrition = Nutrition(1, 2, 3, 4)
    food_id = uuid.uuid4()
    food = Food(
        id=food_id,
        name="Test",
        nutrition=nutrition,
        barcode="123",
        category="Cat",
        default_unit="g",
        units=[UnitInfo("g", 1.0, "gram")],
        owner_id=None,
        source="manual"
    )
    assert food.id == food_id
    assert food.name == "Test"
    assert food.nutrition == nutrition
    assert len(food.units) == 1
