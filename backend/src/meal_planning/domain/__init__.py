"""
Domain layer for meal planning module.

Contains pure domain entities (dataclasses) and port definitions (abstractions).
This layer has no dependencies on infrastructure or external frameworks.
"""
from .entities import (
    ProgressCallback,
    UserProfile,
    MealTemplate,
    GeneratedIngredient,
    GeneratedMeal,
    GeneratedDay,
    GeneratedPlan,
    PlanPreferences,
)
from .ports import MealPlannerPort

__all__ = [
    # Type aliases
    "ProgressCallback",
    # Entities
    "UserProfile",
    "MealTemplate",
    "GeneratedIngredient",
    "GeneratedMeal",
    "GeneratedDay",
    "GeneratedPlan",
    "PlanPreferences",
    # Ports
    "MealPlannerPort",
]
