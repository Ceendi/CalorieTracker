"""
Application layer ports for meal planning module.

Defines repository abstractions to decouple the service layer
from specific infrastructure implementations.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional, Dict, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.meal_planning.domain.entities import GeneratedPlan


class MealPlanRepositoryPort(ABC):
    """
    Port (interface) for meal plan repository.

    Defines the contract for meal plan persistence operations.
    The service layer depends on this abstraction, not the concrete
    SQLAlchemy implementation.
    """

    @abstractmethod
    async def create_plan(
        self,
        user_id: UUID,
        plan: GeneratedPlan,
        name: str,
        start_date: date
    ) -> UUID:
        """
        Create a new meal plan.

        Args:
            user_id: Owner of the plan
            plan: Generated plan to save
            name: Name for the plan
            start_date: Start date of the plan

        Returns:
            UUID of the created plan
        """
        pass

    @abstractmethod
    async def get_plan(self, plan_id: UUID):
        """
        Get a meal plan by ID with all nested relations.

        Args:
            plan_id: ID of the plan to retrieve

        Returns:
            MealPlanModel with all relations loaded, or None if not found
        """
        pass

    @abstractmethod
    async def list_plans(
        self,
        user_id: UUID,
        status: Optional[str] = None
    ) -> List:
        """
        List user's meal plans.

        Args:
            user_id: Owner of the plans
            status: Optional status filter

        Returns:
            List of meal plans (without nested relations)
        """
        pass

    @abstractmethod
    async def delete_plan(self, plan_id: UUID) -> bool:
        """
        Delete a meal plan.

        Args:
            plan_id: ID of the plan to delete

        Returns:
            True if plan was deleted, False if not found
        """
        pass

    @abstractmethod
    async def update_status(self, plan_id: UUID, status: str) -> bool:
        """
        Update the status of a meal plan.

        Args:
            plan_id: ID of the plan to update
            status: New status value

        Returns:
            True if plan was updated, False if not found
        """
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass


class FoodSearchPort(Protocol):
    """
    Port for searching food products using pgvector hybrid search.

    Provides abstraction for searching the food catalogue,
    used by the meal plan service for RAG-based ingredient selection.
    This port is compatible with PgVectorSearchService.
    """

    async def search_for_meal_planning(
        self,
        session: AsyncSession,
        meal_type: str,
        preferences: Optional[Dict] = None,
        limit: int = 40,
        meal_description: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search products suitable for meal planning with nutrition data.

        This is the primary method for RAG-based ingredient retrieval,
        optimized for meal planning context with dietary preferences.

        Args:
            session: Database session for queries
            meal_type: Type of meal (breakfast, lunch, dinner, snack, second_breakfast)
            preferences: Optional dietary preferences dict with keys:
                        - allergies: List[str] - ingredients to avoid
                        - diet: str - "vegetarian", "vegan", etc.
                        - excluded_ingredients: List[str] - specific exclusions
            limit: Maximum number of products to return

        Returns:
            List of dicts with product info and nutrition data:
            - id, name, category, kcal_per_100g, protein_per_100g,
              fat_per_100g, carbs_per_100g, score
        """
        ...

    async def find_product_by_name(
        self,
        session: AsyncSession,
        name: str,
        preferences: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        Find single best matching product by name.

        Used for exact product lookup, e.g., when matching LLM-generated
        meal plan items to database products.

        Args:
            session: Database session for queries
            name: Product name to search for
            preferences: Optional dietary preferences for allergen filtering

        Returns:
            Dict with product info and nutrition, or None if not found
        """
        ...

    async def search_by_category(
        self,
        session: AsyncSession,
        category: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search products by category name.

        Args:
            session: Database session for queries
            category: Category name (e.g., "Nabial", "Owoce")
            limit: Maximum results

        Returns:
            List of product dicts from the specified category
        """
        ...
