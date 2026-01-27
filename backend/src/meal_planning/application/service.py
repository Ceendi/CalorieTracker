"""
Service layer for meal planning module.

Contains business logic for meal plan generation and management,
including BMR/CPM calculations and macro targets.
"""
from dataclasses import dataclass
from datetime import date
from typing import Any, List, Optional
from uuid import UUID

from src.meal_planning.application.ports import MealPlanRepositoryPort
from src.meal_planning.domain.entities import (
    UserProfile,
    PlanPreferences,
    GeneratedPlan,
)
from src.meal_planning.domain.ports import MealPlannerPort


@dataclass
class UserData:
    """
    User data required for meal plan calculations.

    This is a simple data transfer object that contains the user
    attributes needed to calculate BMR, CPM, and daily targets.
    Compatible with the User model from the users module.

    Attributes:
        id: User ID
        weight: Weight in kilograms
        height: Height in centimeters
        age: Age in years
        gender: Gender ('male' or 'female')
        activity_level: Activity level (sedentary, light, moderate, active, very_active)
        goal: Fitness goal (lose, maintain, gain)
    """
    id: UUID
    weight: float
    height: float
    age: int
    gender: str
    activity_level: str
    goal: str


class MealPlanService:
    """
    Service for meal plan generation and management.

    Handles BMR/CPM calculations, daily target generation,
    and coordinates between repository and meal planner.
    """

    # Default meal distribution percentages
    MEAL_DISTRIBUTION = {
        "breakfast": 0.25,
        "second_breakfast": 0.10,
        "lunch": 0.35,
        "snack": 0.10,
        "dinner": 0.20,
    }

    # Default macro ratios
    DEFAULT_PROTEIN_RATIO = 0.30  # 30% calories from protein
    DEFAULT_FAT_RATIO = 0.25      # 25% calories from fat
    DEFAULT_CARBS_RATIO = 0.45   # 45% calories from carbs

    # Activity level multipliers (PAL - Physical Activity Level)
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    # Goal adjustments
    GOAL_ADJUSTMENTS = {
        "lose": 0.8,      # 20% calorie deficit
        "maintain": 1.0,   # No adjustment
        "gain": 1.15,      # 15% calorie surplus
    }

    def __init__(
        self,
        repository: MealPlanRepositoryPort,
        planner: Optional[MealPlannerPort] = None,
    ):
        """
        Initialize the meal plan service.

        Args:
            repository: Repository port for meal plan persistence
            planner: Optional meal planner port for generation (injected later)
        """
        self._repo = repository
        self._planner = planner

    def calculate_daily_targets(
        self,
        user: UserData,
        preferences: PlanPreferences
    ) -> dict:
        """
        Calculate daily macro targets based on user profile.

        Uses Mifflin-St Jeor equation for BMR calculation,
        then applies activity level and goal adjustments.

        Args:
            user: User data with physical attributes
            preferences: Plan preferences (currently unused, for future customization)

        Returns:
            Dict with keys: kcal, protein, fat, carbs
        """
        bmr = self._calculate_bmr(user)
        cpm = bmr * self._get_activity_multiplier(user.activity_level)

        # Apply goal adjustment
        goal_factor = self.GOAL_ADJUSTMENTS.get(user.goal, 1.0)
        daily_kcal = int(cpm * goal_factor)

        # Calculate macros using default ratios
        # Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
        return {
            "kcal": daily_kcal,
            "protein": round(daily_kcal * self.DEFAULT_PROTEIN_RATIO / 4, 1),
            "fat": round(daily_kcal * self.DEFAULT_FAT_RATIO / 9, 1),
            "carbs": round(daily_kcal * self.DEFAULT_CARBS_RATIO / 4, 1),
        }

    def build_user_profile(
        self,
        user: UserData,
        preferences: PlanPreferences
    ) -> UserProfile:
        """
        Build a UserProfile for the meal planner.

        Combines calculated targets with user preferences
        into a profile suitable for meal plan generation.

        Args:
            user: User data with physical attributes
            preferences: Plan preferences

        Returns:
            UserProfile entity for the planner
        """
        targets = self.calculate_daily_targets(user, preferences)

        return UserProfile(
            user_id=user.id,
            daily_kcal=targets["kcal"],
            daily_protein=targets["protein"],
            daily_fat=targets["fat"],
            daily_carbs=targets["carbs"],
            preferences={
                "diet": preferences.diet,
                "allergies": preferences.allergies,
                "cuisine_preferences": preferences.cuisine_preferences,
                "excluded_ingredients": preferences.excluded_ingredients,
            }
        )

    def _calculate_bmr(self, user: UserData) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Formula:
        - Male: BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        - Female: BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

        Args:
            user: User data with weight, height, age, and gender

        Returns:
            BMR in kcal/day
        """
        base = 10 * user.weight + 6.25 * user.height - 5 * user.age
        if user.gender == "male":
            return base + 5
        else:
            return base - 161

    def _get_activity_multiplier(self, level: str) -> float:
        """
        Get the Physical Activity Level (PAL) multiplier.

        Args:
            level: Activity level string

        Returns:
            PAL multiplier (defaults to 'moderate' if unknown)
        """
        return self.ACTIVITY_MULTIPLIERS.get(level, 1.55)

    # Repository pass-through methods with authorization checks

    async def save_plan(
        self,
        user_id: UUID,
        plan: GeneratedPlan,
        name: str,
        start_date: date
    ) -> UUID:
        """
        Save a generated plan for a user.

        Args:
            user_id: Owner of the plan
            plan: Generated plan to save
            name: Name for the plan
            start_date: Start date of the plan

        Returns:
            UUID of the created plan
        """
        plan_id = await self._repo.create_plan(user_id, plan, name, start_date)
        await self._repo.commit()
        return plan_id

    async def get_plan(
        self,
        plan_id: UUID,
        user_id: UUID
    ) -> Optional[Any]:
        """
        Get a meal plan by ID with authorization check.

        Args:
            plan_id: ID of the plan
            user_id: ID of the requesting user

        Returns:
            Meal plan if found and user is authorized, None otherwise
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            return plan
        return None

    async def list_plans(
        self,
        user_id: UUID,
        status: Optional[str] = None
    ) -> List[Any]:
        """
        List all meal plans for a user.

        Args:
            user_id: Owner of the plans
            status: Optional status filter

        Returns:
            List of meal plans
        """
        return await self._repo.list_plans(user_id, status)

    async def delete_plan(
        self,
        plan_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a meal plan with authorization check.

        Args:
            plan_id: ID of the plan to delete
            user_id: ID of the requesting user

        Returns:
            True if deleted, False if not found or unauthorized
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            result = await self._repo.delete_plan(plan_id)
            await self._repo.commit()
            return result
        return False

    async def update_plan_status(
        self,
        plan_id: UUID,
        user_id: UUID,
        status: str
    ) -> bool:
        """
        Update the status of a meal plan with authorization check.

        Args:
            plan_id: ID of the plan
            user_id: ID of the requesting user
            status: New status value

        Returns:
            True if updated, False if not found or unauthorized
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            result = await self._repo.update_status(plan_id, status)
            await self._repo.commit()
            return result
        return False
