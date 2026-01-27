"""
Dependencies for meal planning API endpoints.

Provides dependency injection for services and authentication.
"""
from typing import Optional

from src.core.database import DBSession
from src.meal_planning.application.service import MealPlanService
from src.meal_planning.infrastructure.repository import MealPlanRepository
from src.meal_planning.infrastructure.food_search_adapter import SqlAlchemyFoodSearchAdapter
from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter

# Re-export current_active_user from users module for convenience
from src.users.api.routes import current_active_user as get_current_user

# Singleton instance of the Bielik planner (lazy loaded)
_bielik_planner: Optional[BielikMealPlannerAdapter] = None


def get_meal_planner() -> BielikMealPlannerAdapter:
    """
    Get singleton Bielik meal planner instance.

    Uses lazy initialization to avoid loading the model until needed.

    Returns:
        BielikMealPlannerAdapter instance
    """
    global _bielik_planner
    if _bielik_planner is None:
        _bielik_planner = BielikMealPlannerAdapter()
    return _bielik_planner


async def get_meal_plan_service(
    session: DBSession,
) -> MealPlanService:
    """
    Create MealPlanService with injected dependencies.

    Injects:
    - Repository for persistence
    - BielikMealPlannerAdapter for LLM-based generation
    - SqlAlchemyFoodSearchAdapter for RAG product search

    Args:
        session: Database session from dependency injection

    Returns:
        Configured MealPlanService instance
    """
    repository = MealPlanRepository(session)
    food_search = SqlAlchemyFoodSearchAdapter(session)
    planner = get_meal_planner()

    return MealPlanService(
        repository=repository,
        planner=planner,
        food_search=food_search
    )
