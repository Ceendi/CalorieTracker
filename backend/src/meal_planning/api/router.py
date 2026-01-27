"""
Router for meal planning API endpoints.

Provides CRUD operations for meal plans and daily targets calculation.
Generation endpoint will be added in PART 6.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.meal_planning.api.dependencies import get_meal_plan_service, get_current_user
from src.meal_planning.api.schemas import (
    MealPlanSchema,
    MealPlanListResponse,
    MealPlanSummarySchema,
    DailyTargetsResponse,
    PlanPreferencesSchema,
)
from src.meal_planning.application.service import MealPlanService, UserData
from src.meal_planning.domain.entities import PlanPreferences
from src.users.domain.models import User


router = APIRouter(prefix="/meal-plans", tags=["Meal Planning"])


def _validate_user_profile(user: User) -> None:
    """
    Validate that user has completed their profile.

    Raises HTTPException 400 if required fields are missing.
    """
    if not all([user.weight, user.height, user.age]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your profile first. Required: weight, height, age."
        )


def _user_to_user_data(user: User) -> UserData:
    """
    Map User model to UserData DTO for service layer.

    Args:
        user: User model from authentication

    Returns:
        UserData DTO for meal plan calculations
    """
    return UserData(
        id=user.id,
        weight=user.weight,
        height=user.height,
        age=user.age,
        gender=user.gender or "female",  # Default if not set
        activity_level=user.activity_level or "moderate",  # Default if not set
        goal=user.goal or "maintain",  # Default if not set
    )


@router.get("", response_model=MealPlanListResponse)
async def list_meal_plans(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: MealPlanService = Depends(get_meal_plan_service),
):
    """
    List all meal plans for the current user.

    Args:
        status_filter: Optional filter by status (draft, active, archived)
        current_user: Authenticated user
        service: Meal plan service

    Returns:
        List of meal plan summaries
    """
    plans = await service.list_plans(current_user.id, status=status_filter)
    return MealPlanListResponse(
        plans=[MealPlanSummarySchema.model_validate(p) for p in plans]
    )


@router.get("/daily-targets", response_model=DailyTargetsResponse)
async def get_daily_targets(
    diet: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: MealPlanService = Depends(get_meal_plan_service),
):
    """
    Calculate daily macro targets for the current user.

    Uses Mifflin-St Jeor equation for BMR, then applies
    activity level and goal adjustments.

    Args:
        diet: Optional diet type (currently unused, for future customization)
        current_user: Authenticated user with profile data
        service: Meal plan service

    Returns:
        Daily targets (kcal, protein, fat, carbs)

    Raises:
        HTTPException 400: If user profile is incomplete
    """
    _validate_user_profile(current_user)

    user_data = _user_to_user_data(current_user)

    # Create minimal preferences (diet parameter reserved for future use)
    preferences = PlanPreferences(diet=diet)

    targets = service.calculate_daily_targets(user_data, preferences)
    return DailyTargetsResponse(**targets)


@router.get("/{plan_id}", response_model=MealPlanSchema)
async def get_meal_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MealPlanService = Depends(get_meal_plan_service),
):
    """
    Get a specific meal plan with all details.

    Args:
        plan_id: ID of the meal plan
        current_user: Authenticated user
        service: Meal plan service

    Returns:
        Full meal plan with days, meals, and ingredients

    Raises:
        HTTPException 404: If plan not found or not owned by user
    """
    plan = await service.get_plan(plan_id, current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    return MealPlanSchema.from_orm_model(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MealPlanService = Depends(get_meal_plan_service),
):
    """
    Delete a meal plan.

    Args:
        plan_id: ID of the meal plan to delete
        current_user: Authenticated user
        service: Meal plan service

    Raises:
        HTTPException 404: If plan not found or not owned by user
    """
    deleted = await service.delete_plan(plan_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal plan not found"
        )
    return None
