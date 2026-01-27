"""
Dependencies for meal planning API endpoints.

Provides dependency injection for services and authentication.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import DBSession
from src.meal_planning.application.service import MealPlanService
from src.meal_planning.infrastructure.repository import MealPlanRepository

# Re-export current_active_user from users module for convenience
from src.users.api.routes import current_active_user as get_current_user


async def get_meal_plan_service(
    session: DBSession,
) -> MealPlanService:
    """
    Create MealPlanService with injected repository.

    Args:
        session: Database session from dependency injection

    Returns:
        Configured MealPlanService instance
    """
    repository = MealPlanRepository(session)
    return MealPlanService(repository=repository)
