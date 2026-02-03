import asyncio
import os
import sys
from unittest.mock import MagicMock

import pytest

# Add backend to path so we can import config
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import MealTemplate, UserProfile

@pytest.mark.asyncio
async def test_meal_generation_calorie_parsing():
    print("Running calorie parsing test (standalone)...")
    adapter = BielikMealPlannerAdapter()
    
    # Mock the LLM response with "100g" string which caused issues
    mock_json = """
    {
        "name": "Test Meal",
        "description": "Test description",
        "preparation_time": 15,
        "ingredients": [
            {
                "name": "Kurczak",
                "amount_grams": "100g", 
                "unit_label": "100 g"
            },
            {
                "name": "Ryż",
                "amount": "50 g",
                "unit_label": "50 g"
            }
        ]
    }
    """
    
    mock_llm_response = {
        "choices": [{
            "text": f"Here is the JSON:\n```json\n{mock_json}\n```"
        }]
    }
    
    # Mock dependencies
    # We mock _get_model to return a callable that returns our response
    mock_model = MagicMock()
    mock_model.return_value = mock_llm_response
    adapter._get_model = MagicMock(return_value=mock_model)
    
    available_products = [
        {"id": "1", "name": "Kurczak", "kcal_per_100g": 100, "protein_per_100g": 20, "fat_per_100g": 5, "carbs_per_100g": 0},
        {"id": "2", "name": "Ryż", "kcal_per_100g": 350, "protein_per_100g": 7, "fat_per_100g": 1, "carbs_per_100g": 78}
    ]
    
    template = MealTemplate("lunch", 500, 30, 20, 50, "Test lunch")
    profile = UserProfile(user_id="123", daily_kcal=2000, daily_protein=150, daily_fat=60, daily_carbs=200)
    
    try:
        meal = await adapter.generate_meal(template, profile, [], available_products)
        
        chicken = next(i for i in meal.ingredients if i.name == "Kurczak")
        rice = next(i for i in meal.ingredients if i.name == "Ryż")
        
        print(f"Chicken amount: {chicken.amount_grams} (Expected 100.0)")
        print(f"Rice amount: {rice.amount_grams} (Expected 50.0)")
        print(f"Total Kcal: {meal.total_kcal} (Expected ~275.0)")
        
        if chicken.amount_grams != 100.0 or rice.amount_grams != 50.0:
            print("FAILED: Parsing error.")
        else:
            print("SUCCESS: Parsing logic verified.")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_meal_generation_calorie_parsing())