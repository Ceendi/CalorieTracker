"""
Application layer ports for meal planning module.

Defines repository abstractions to decouple the service layer
from specific infrastructure implementations.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID

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


class FoodSearchPort(ABC):
    """
    Port for searching food products.

    Provides abstraction for searching the food catalogue,
    used by the meal plan service for RAG-based ingredient selection.
    """

    @abstractmethod
    async def search_products(
        self,
        query: str,
        limit: int = 20
    ) -> List[dict]:
        """
        Search for food products by name.

        Args:
            query: Search query (ingredient name or description)
            limit: Maximum number of results

        Returns:
            List of product dicts with keys: id, name, kcal_per_100g,
            protein_per_100g, fat_per_100g, carbs_per_100g, category
        """
        pass

    @abstractmethod
    async def get_products_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get products by category.

        Args:
            category: Food category to filter by
            limit: Maximum number of results

        Returns:
            List of product dicts
        """
        pass
