"""
Shared fixtures and factory functions for meal_planning unit tests.
"""
import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock

from src.meal_planning.application.service import MealPlanService, UserData
from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import (
    GeneratedIngredient,
    GeneratedMeal,
    GeneratedDay,
    GeneratedPlan,
    MealTemplate,
    UserProfile,
    PlanPreferences,
)


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_ingredient(
    name: str = "Test Ingredient",
    food_id: UUID = None,
    amount_grams: float = 100.0,
    kcal: float = 100.0,
    protein: float = 10.0,
    fat: float = 5.0,
    carbs: float = 15.0,
    unit_label: str = None,
    *,
    auto_food_id: bool = True,
) -> GeneratedIngredient:
    """Create a test ingredient. If auto_food_id=True and food_id is None, a random UUID is assigned."""
    if food_id is None and auto_food_id:
        food_id = uuid4()
    return GeneratedIngredient(
        food_id=food_id,
        name=name,
        amount_grams=amount_grams,
        unit_label=unit_label,
        kcal=kcal,
        protein=protein,
        fat=fat,
        carbs=carbs,
    )


def make_meal(
    meal_type: str = "breakfast",
    ingredients: list = None,
    total_kcal: float = None,
    name: str = "Test Meal",
) -> GeneratedMeal:
    """Create a test meal. Totals default to sum of ingredients."""
    if ingredients is None:
        ingredients = [make_ingredient()]
    if total_kcal is None:
        total_kcal = sum(i.kcal for i in ingredients)
    return GeneratedMeal(
        meal_type=meal_type,
        name=name,
        description="Test",
        preparation_time_minutes=15,
        ingredients=ingredients,
        total_kcal=total_kcal,
        total_protein=sum(i.protein for i in ingredients),
        total_fat=sum(i.fat for i in ingredients),
        total_carbs=sum(i.carbs for i in ingredients),
    )


def make_day(day_number: int = 1, meals: list = None) -> GeneratedDay:
    """Create a test day with default three meals."""
    if meals is None:
        meals = [
            make_meal("breakfast", total_kcal=500),
            make_meal("lunch", total_kcal=700),
            make_meal("dinner", total_kcal=400),
        ]
    return GeneratedDay(day_number=day_number, meals=meals)


def make_plan(days: list = None) -> GeneratedPlan:
    """Create a test plan."""
    if days is None:
        days = [make_day(1), make_day(2)]
    return GeneratedPlan(
        days=days,
        preferences_applied={},
        generation_metadata={},
    )


def make_user_data(
    id: UUID = None,
    weight: float = 80.0,
    height: float = 180.0,
    age: int = 30,
    gender: str = "male",
    activity_level: str = "moderate",
    goal: str = "maintain",
) -> UserData:
    """Create a test UserData DTO."""
    return UserData(
        id=id or uuid4(),
        weight=weight,
        height=height,
        age=age,
        gender=gender,
        activity_level=activity_level,
        goal=goal,
    )


def make_template(
    meal_type: str = "breakfast",
    target_kcal: int = 500,
    target_protein: float = 25.0,
    target_fat: float = 15.0,
    target_carbs: float = 60.0,
    description: str = "Sniadanie",
    ingredient_keywords: list = None,
) -> MealTemplate:
    """Create a test MealTemplate."""
    return MealTemplate(
        meal_type=meal_type,
        target_kcal=target_kcal,
        target_protein=target_protein,
        target_fat=target_fat,
        target_carbs=target_carbs,
        description=description,
        ingredient_keywords=ingredient_keywords or [],
    )


def make_profile(
    user_id: UUID = None,
    daily_kcal: int = 2000,
    daily_protein: float = 150.0,
    daily_fat: float = 55.0,
    daily_carbs: float = 225.0,
    preferences: dict = None,
) -> UserProfile:
    """Create a test UserProfile."""
    return UserProfile(
        user_id=user_id or uuid4(),
        daily_kcal=daily_kcal,
        daily_protein=daily_protein,
        daily_fat=daily_fat,
        daily_carbs=daily_carbs,
        preferences=preferences or {},
    )


def make_product(
    id: str = None,
    name: str = "Test Product",
    category: str = "Zboza",
    kcal_per_100g: float = 200.0,
    protein_per_100g: float = 10.0,
    fat_per_100g: float = 5.0,
    carbs_per_100g: float = 30.0,
    score: float = None,
) -> dict:
    """Create a test product dict (as returned by RAG search)."""
    product = {
        "id": id or str(uuid4()),
        "name": name,
        "category": category,
        "kcal_per_100g": kcal_per_100g,
        "protein_per_100g": protein_per_100g,
        "fat_per_100g": fat_per_100g,
        "carbs_per_100g": carbs_per_100g,
    }
    if score is not None:
        product["score"] = score
    return product


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    """MealPlanService with mocked repository."""
    mock_repo = MagicMock()
    return MealPlanService(repository=mock_repo)


@pytest.fixture
def adapter():
    """BielikMealPlannerAdapter (without model loading)."""
    a = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
    a._model = None
    a._embedding_service = None
    return a


@pytest.fixture
def default_preferences():
    """Default PlanPreferences."""
    return PlanPreferences()


@pytest.fixture
def sample_products():
    """Five common test products."""
    return [
        make_product(
            id="11111111-1111-1111-1111-111111111111",
            name="Platki owsiane",
            category="Zboza",
            kcal_per_100g=372,
            protein_per_100g=13.5,
            fat_per_100g=6.5,
            carbs_per_100g=58.0,
        ),
        make_product(
            id="22222222-2222-2222-2222-222222222222",
            name="Mleko 2%",
            category="Nabial",
            kcal_per_100g=50,
            protein_per_100g=3.4,
            fat_per_100g=2.0,
            carbs_per_100g=4.8,
        ),
        make_product(
            id="33333333-3333-3333-3333-333333333333",
            name="Banan",
            category="Owoce",
            kcal_per_100g=89,
            protein_per_100g=1.1,
            fat_per_100g=0.3,
            carbs_per_100g=22.8,
        ),
        make_product(
            id="44444444-4444-4444-4444-444444444444",
            name="Kurczak piersi",
            category="Drob",
            kcal_per_100g=165,
            protein_per_100g=31.0,
            fat_per_100g=3.6,
            carbs_per_100g=0.0,
        ),
        make_product(
            id="55555555-5555-5555-5555-555555555555",
            name="Ryz bialy",
            category="Zboza",
            kcal_per_100g=130,
            protein_per_100g=2.7,
            fat_per_100g=0.3,
            carbs_per_100g=28.0,
        ),
    ]
