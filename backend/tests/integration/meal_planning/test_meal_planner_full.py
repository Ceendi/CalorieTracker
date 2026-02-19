
import pytest
import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import UserProfile, GeneratedDay, GeneratedMeal, GeneratedIngredient

@pytest.mark.asyncio
async def test_full_plan_optimization():
    print("Running full plan optimization test...")
    adapter = BielikMealPlannerAdapter()
    
    # Setup: Create a generated day with low calories (~1000 kcal)
    # Target is 2500 kcal
    
    # 100g Chicken = 100 kcal
    # 100g Rice = 130 kcal
    # Total Meal = 230 kcal
    # 5 Meals = 1150 kcal
    
    # Create 5 DISTINCT meal objects to avoid reference sharing issues during scaling
    meals = []
    for i in range(5):
        meals.append(GeneratedMeal(
            meal_type="lunch",
            name=f"Low Calorie Meal {i}",
            description="Test",
            preparation_time_minutes=15,
            ingredients=[
                GeneratedIngredient(None, "Kurczak", 100.0, "100g", 100.0, 20.0, 5.0, 0.0),
                GeneratedIngredient(None, "Ryż", 100.0, "100g", 130.0, 3.0, 0.0, 28.0)
            ],
            total_kcal=230.0,
            total_protein=23.0,
            total_fat=5.0,
            total_carbs=28.0
        ))
    
    day = GeneratedDay(
        day_number=1,
        meals=meals
    )
    
    # Initial check
    print(f"Initial Daily Kcal: {day.total_kcal}")
    assert day.total_kcal == 1150.0
    
    # Profile with high target
    profile = UserProfile(
        user_id="123",
        daily_kcal=2500,
        daily_protein=150,
        daily_fat=80,
        daily_carbs=300
    )
    
    # Run optimization
    optimized_days = await adapter.optimize_plan([day], profile)
    optimized_day = optimized_days[0]
    
    print(f"Optimized Daily Kcal: {optimized_day.total_kcal}")
    
    # Expected scaling: 2500 / 1150 = 2.17
    # Should be close to 2500
    assert abs(optimized_day.total_kcal - 2500.0) < 50.0, f"Optimization failed. Got {optimized_day.total_kcal}, expected ~2500"
    
    # Check ingredient scaling
    # Chicken should be 100g * 2.17 = 217g
    new_chicken = optimized_day.meals[0].ingredients[0]
    print(f"New Chicken Amount: {new_chicken.amount_grams:.2f}")
    assert new_chicken.amount_grams > 200.0, "Ingredient amounts not scaled up"

if __name__ == "__main__":
    asyncio.run(test_full_plan_optimization())
