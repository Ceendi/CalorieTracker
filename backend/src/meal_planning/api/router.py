"""
Router for meal planning API endpoints.

Provides CRUD operations for meal plans, daily targets calculation,
and async meal plan generation with SSE progress tracking.
"""
import asyncio
import json
from typing import Dict, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from src.meal_planning.api.dependencies import get_meal_plan_service, get_current_user
from src.meal_planning.api.schemas import (
    MealPlanSchema,
    MealPlanListResponse,
    MealPlanSummarySchema,
    DailyTargetsResponse,
    PlanPreferencesSchema,
    GeneratePlanRequest,
    GeneratePlanResponse,
)
from src.meal_planning.application.service import MealPlanService, UserData
from src.meal_planning.domain.entities import PlanPreferences
from src.users.domain.models import User


router = APIRouter(prefix="/meal-plans", tags=["Meal Planning"])

# In-memory progress storage for generation tasks
# Format: {task_id: {"status": "...", "progress": 0-100, ...}}
# Note: In production, use Redis or similar for multi-instance support
_generation_progress: Dict[str, dict] = {}


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


@router.post("/generate", response_model=GeneratePlanResponse)
async def generate_meal_plan(
    request: GeneratePlanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: MealPlanService = Depends(get_meal_plan_service),
):
    """
    Start async meal plan generation.

    Starts generation in background and returns a task_id that can be used
    to track progress via the SSE endpoint.

    Args:
        request: Generation request with preferences
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        service: Meal plan service

    Returns:
        Task ID for progress tracking

    Raises:
        HTTPException 400: If user profile is incomplete
    """
    _validate_user_profile(current_user)

    task_id = str(uuid4())
    _generation_progress[task_id] = {
        "status": "started",
        "progress": 0,
        "message": "Rozpoczynam generowanie planu..."
    }

    # Capture user data before background task
    user_data = _user_to_user_data(current_user)
    user_id = current_user.id

    async def progress_callback(update: dict):
        """Update progress in memory storage."""
        _generation_progress[task_id] = {
            **update,
            "status": "generating"
        }

    async def generate():
        """Background task for plan generation."""
        try:
            preferences = PlanPreferences(
                diet=request.preferences.diet,
                allergies=request.preferences.allergies,
                cuisine_preferences=request.preferences.cuisine_preferences,
                excluded_ingredients=request.preferences.excluded_ingredients,
                max_preparation_time=request.preferences.max_preparation_time,
            )

            plan = await service.generate_plan(
                user=user_data,
                preferences=preferences,
                start_date=request.start_date,
                days=request.days,
                progress_callback=progress_callback
            )

            plan_name = request.name or f"Plan od {request.start_date}"
            plan_id = await service.save_plan(
                user_id=user_id,
                plan=plan,
                name=plan_name,
                start_date=request.start_date
            )

            _generation_progress[task_id] = {
                "status": "completed",
                "progress": 100,
                "plan_id": str(plan_id),
                "message": "Plan zostal wygenerowany pomyslnie"
            }

            logger.info(f"Plan generation completed: task={task_id}, plan={plan_id}")

        except Exception as e:
            logger.error(f"Plan generation failed: task={task_id}, error={e}")
            _generation_progress[task_id] = {
                "status": "error",
                "message": "Blad podczas generowania planu"
            }

    # Schedule the generation task
    background_tasks.add_task(generate)

    logger.info(f"Started plan generation: task={task_id}, user={user_id}")

    return GeneratePlanResponse(
        task_id=task_id,
        message="Generation started. Use /generate/{task_id}/progress to track progress."
    )


@router.get("/generate/{task_id}/progress")
async def get_generation_progress(task_id: str):
    """
    SSE endpoint for tracking generation progress.

    Returns a Server-Sent Events stream with progress updates.
    The stream ends when status is "completed" or "error".

    Event format:
    ```
    data: {"status": "generating", "progress": 50, "day": 3, "message": "..."}

    ```

    Args:
        task_id: Task ID from /generate endpoint

    Returns:
        StreamingResponse with text/event-stream content
    """

    async def event_stream():
        """Generate SSE events until completion or error."""
        while True:
            progress = _generation_progress.get(task_id, {"status": "unknown"})

            # Send progress update
            yield f"data: {json.dumps(progress)}\n\n"

            # Check if generation is complete
            if progress.get("status") in ["completed", "error", "unknown"]:
                # Clean up after a short delay to allow client to receive final event
                if progress.get("status") != "unknown":
                    await asyncio.sleep(1)
                    _generation_progress.pop(task_id, None)
                break

            # Wait before next update
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/generate/{task_id}/status")
async def get_generation_status(task_id: str):
    """
    Get current generation status (non-streaming alternative).

    Useful for polling-based clients that don't support SSE.

    Args:
        task_id: Task ID from /generate endpoint

    Returns:
        Current progress status
    """
    progress = _generation_progress.get(task_id)

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or already completed"
        )

    return progress
