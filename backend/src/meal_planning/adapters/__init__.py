"""
Adapters for meal planning module.

Contains implementations of ports for external services like LLM providers.
"""

from .bielik_meal_planner import BielikMealPlannerAdapter

__all__ = ["BielikMealPlannerAdapter"]
