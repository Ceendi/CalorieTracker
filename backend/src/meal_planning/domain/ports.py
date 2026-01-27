"""
Port definitions for meal planning module.

Ports define abstractions (interfaces) for external dependencies,
allowing the domain layer to remain independent of specific implementations.
"""
from abc import ABC, abstractmethod
from typing import List

from .entities import (
    UserProfile,
    MealTemplate,
    GeneratedMeal,
    GeneratedDay,
)


class MealPlannerPort(ABC):
    """
    Port for meal plan generation.

    Defines the contract for LLM-based meal plan generation.
    Allows swapping implementations (e.g., Bielik, OpenAI, mock for testing).

    The meal generation flow:
    1. generate_meal_templates() - Creates structure/templates for each day
    2. generate_meal() - Fills each template with actual ingredients
    3. optimize_plan() - Balances the complete plan for variety and targets
    """

    @abstractmethod
    async def generate_meal_templates(
        self,
        profile: UserProfile,
        days: int = 7
    ) -> List[List[MealTemplate]]:
        """
        Generate meal structure templates for each day.

        This is the first step of plan generation. The LLM creates
        a high-level structure with meal descriptions and target macros.

        Args:
            profile: User profile with daily targets and preferences
            days: Number of days to generate (default: 7)

        Returns:
            List of days, where each day is a list of meal templates.
            Example: [[breakfast_template, lunch_template, ...], ...]
        """
        pass

    @abstractmethod
    async def generate_meal(
        self,
        template: MealTemplate,
        profile: UserProfile,
        used_ingredients: List[str],
        available_products: List[dict]
    ) -> GeneratedMeal:
        """
        Generate a single meal with ingredients from available products.

        Uses RAG to select ingredients from the database and compose
        a complete meal that matches the template's targets.

        Args:
            template: Meal template to fill with ingredients
            profile: User profile for preferences
            used_ingredients: Recently used ingredient names (for variety)
            available_products: Products from RAG search (dicts with name, nutrition)

        Returns:
            Complete meal with ingredients and calculated nutrition
        """
        pass

    @abstractmethod
    async def optimize_plan(
        self,
        days: List[GeneratedDay],
        profile: UserProfile
    ) -> List[GeneratedDay]:
        """
        Optimize the complete plan for variety and nutritional balance.

        Adjusts portions to better hit macro targets and ensures
        variety across the plan.

        Args:
            days: Generated days to optimize
            profile: User profile with target macros

        Returns:
            Optimized list of days with adjusted portions
        """
        pass
