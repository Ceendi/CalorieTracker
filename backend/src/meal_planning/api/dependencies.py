"""
Dependencies for meal planning API endpoints.

Provides dependency injection for services and authentication.
"""
from typing import Optional

from src.core.database import DBSession
from src.meal_planning.application.service import MealPlanService
from src.meal_planning.infrastructure.repository import MealPlanRepository
from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.ai.infrastructure.search import PgVectorSearchService
from src.ai.infrastructure.embedding import get_embedding_service

# Re-export current_active_user from users module for convenience
from src.users.api.routes import current_active_user as get_current_user

# Singleton instance of the Bielik planner (lazy loaded)
_bielik_planner: Optional[BielikMealPlannerAdapter] = None

# Singleton instance of the food search service (lazy loaded)
_food_search_service: Optional[PgVectorSearchService] = None


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


def get_food_search_service() -> PgVectorSearchService:
    """
    Get singleton PgVectorSearchService instance.

    This replaces the old SqlAlchemyFoodSearchAdapter with the new
    pgvector-based hybrid search that combines:
    - Vector similarity search (cosine distance) via pgvector
    - Full-text search (tsvector/tsquery) via PostgreSQL
    - Reciprocal Rank Fusion (RRF) for score combination

    Returns:
        PgVectorSearchService instance
    """
    global _food_search_service
    if _food_search_service is None:
        embedding_service = get_embedding_service()
        _food_search_service = PgVectorSearchService(embedding_service)
    return _food_search_service


async def get_meal_plan_service(
    session: DBSession,
) -> MealPlanService:
    """
    Create MealPlanService with injected dependencies.

    Injects:
    - Repository for persistence
    - BielikMealPlannerAdapter for LLM-based generation
    - PgVectorSearchService for pgvector-based RAG product search
    - Database session for search queries

    Args:
        session: Database session from dependency injection

    Returns:
        Configured MealPlanService instance
    """
    repository = MealPlanRepository(session)
    food_search = get_food_search_service()
    planner = get_meal_planner()

    return MealPlanService(
        repository=repository,
        planner=planner,
        food_search=food_search,
        session=session  # Required for PgVectorSearchService queries
    )
