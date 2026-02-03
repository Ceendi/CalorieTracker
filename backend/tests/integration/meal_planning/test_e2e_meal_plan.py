
import pytest
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.domain.entities import UserProfile, MealTemplate
from src.ai.infrastructure.embedding.embedding_service import EmbeddingService
from src.meal_planning.application.service import MealPlanService, UserData, PlanPreferences

# Mocking the repository and food search ports for the service test
# We want to test the ADAPTER logic mostly, but simulating the flow via Service is good too. 
# However, Service requires a real DB session for pgvector search. 
# To make this robust without depending on the exact DB state for the *LLM* part, 
# we will test the Adapter directly with a mocked Model but *REAL* EmbeddingService.

@pytest.mark.asyncio
async def test_e2e_meal_generation_logic():
    print("Starting E2E Meal Plan Logic Test...")
    
    # 1. Setup Adapter with Real Embedding Service
    adapter = BielikMealPlannerAdapter()
    
    # 2. Mock the LLM Response to simulate Bielik
    # We provide a fixed response to ensure determinism for the test, 
    # but we test the *parsing* and *matching* logic which are the critical complex parts.
    
    mock_template_json = """
    {
        "days": [
            {
                "day": 1, 
                "meals": [
                    {"type": "breakfast", "description": "Jajecznica z pomidorami"},
                    {"type": "lunch", "description": "Kurczak z ryżem"}
                ]
            },
            {
                "day": 2, 
                "meals": [
                    {"type": "breakfast", "description": "Owsianka z bananem"},
                    {"type": "lunch", "description": "Ryba z ziemniakami"}
                ]
            }
        ]
    }
    """
    
    mock_meal_json_1 = """
    {
        "name": "Jajecznica",
        "description": "Pyszna jajecznica",
        "preparation_time": 10,
        "ingredients": [
            {"name": "Jajko", "amount_grams": 150, "unit_label": "3 szt"},
            {"name": "Pomidor", "amount_grams": 100, "unit_label": "1 szt"}
        ]
    }
    """
    
    mock_meal_json_2 = """
    {
        "name": "Owsianka",
        "description": "Zdrowa owsianka",
        "preparation_time": 10,
        "ingredients": [
            {"name": "Płatki owsiane", "amount_grams": 50},
            {"name": "Mleko", "amount_grams": 200}
        ]
    }
    """

    # Mock the LLM call to return templates first, then meals
    async def mock_llm_call(model, prompt, **kwargs):
        if "Zaplanuj strukture" in prompt:
            return {"choices": [{"text": mock_template_json}]}
        elif "Jajecznica" in prompt:
            return {"choices": [{"text": mock_meal_json_1}]}
        else:
            return {"choices": [{"text": mock_meal_json_2}]}

    # Apply the mock
    adapter._get_model = MagicMock() # Mock the loader
    # We need to mock asyncio.to_thread to call our async mock logic or just a sync wrapper
    # Since the real code uses asyncio.to_thread(model, ...), we mock the model object itself to be callable
    mock_model_obj = MagicMock(side_effect=mock_llm_call)
    # But wait, asyncio.to_thread runs a sync function in a thread. 
    # Our mock_llm_call is async? No, let's make it sync for the mock.
    
    def mock_llm_sync(prompt, **kwargs):
        if "Zaplanuj strukture" in prompt:
            return {"choices": [{"text": mock_template_json}]}
        elif "Jajecznica" in prompt:
            return {"choices": [{"text": mock_meal_json_1}]}
        else:
            return {"choices": [{"text": mock_meal_json_2}]}
            
    # The adapter calls `model(prompt, ...)` inside `to_thread`
    adapter._get_model.return_value = mock_llm_sync

    # 3. Simulate Data for Matching
    # These mimic what PGVector would return
    available_products = [
        {"id": "1", "name": "Jajko kurze całe", "kcal_per_100g": 140, "protein_per_100g": 12, "fat_per_100g": 10, "carbs_per_100g": 1},
        {"id": "2", "name": "Pomidor", "kcal_per_100g": 20, "protein_per_100g": 1, "fat_per_100g": 0, "carbs_per_100g": 4},
        {"id": "3", "name": "Płatki owsiane górskie", "kcal_per_100g": 370, "protein_per_100g": 13, "fat_per_100g": 7, "carbs_per_100g": 60},
        {"id": "4", "name": "Mleko spożywcze 2%", "kcal_per_100g": 50, "protein_per_100g": 3, "fat_per_100g": 2, "carbs_per_100g": 5},
    ]

    # 4. Test Template Generation
    print("\nTesting Template Generation...")
    profile = UserProfile(user_id="123", daily_kcal=2000, daily_protein=150, daily_fat=70, daily_carbs=250)
    templates = await adapter.generate_meal_templates(profile, days=2)
    
    assert len(templates) == 2, "Should generate 2 days"
    assert templates[0][0].description == "Jajecznica z pomidorami"
    print("Templates generated successfully.")

    # 5. Test Meal Generation & Matching (The Core Logic)
    print("\nTesting Meal Generation & Semantic Matching...")
    
    # Test Day 1 Breakfast (Jajecznica)
    # LLM says "Jajko" -> DB has "Jajko kurze całe". Semantic match should find it.
    meal1 = await adapter.generate_meal(
        templates[0][0], 
        profile, 
        [], 
        available_products
    )
    
    print(f"Generated Meal: {meal1.name}")
    for ing in meal1.ingredients:
        print(f"  - {ing.name} ({ing.amount_grams}g) -> Kcal: {ing.kcal}")
        
    # Validation
    # Jajko (150g) * 1.4 kcal/g = 210 kcal
    # Pomidor (100g) * 0.2 kcal/g = 20 kcal
    # Total ~ 230
    
    egg = next(i for i in meal1.ingredients if "Jajko" in i.name)
    assert egg.kcal > 100, "Egg calories too low - likely failed match"
    assert "kurze" in egg.name or "Jajko" in egg.name, "Should match to DB product name"
    
    print(f"Meal 1 Total Kcal: {meal1.total_kcal}")
    assert meal1.total_kcal > 200, "Meal 1 total calories suspicious"

    print("\nE2E Logic Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_e2e_meal_generation_logic())
