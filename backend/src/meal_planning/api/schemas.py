"""
Pydantic schemas for meal planning API.

Contains request/response models for the meal planning endpoints.
All schemas use from_attributes = True for ORM model mapping.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PlanPreferencesSchema(BaseModel):
    """
    User preferences for meal plan generation.

    Used as input when generating or calculating targets.
    """
    diet: Optional[str] = Field(
        default=None,
        description="Diet type: vegetarian, vegan, keto, etc."
    )
    allergies: List[str] = Field(
        default_factory=list,
        description="List of allergens to avoid"
    )
    cuisine_preferences: List[str] = Field(
        default_factory=lambda: ["polish"],
        description="Preferred cuisines"
    )
    excluded_ingredients: List[str] = Field(
        default_factory=list,
        description="Specific ingredients to exclude"
    )
    max_preparation_time: Optional[int] = Field(
        default=None,
        description="Maximum preparation time per meal in minutes"
    )


class GeneratePlanRequest(BaseModel):
    """Request body for meal plan generation."""
    name: Optional[str] = Field(
        default=None,
        description="Optional name for the plan"
    )
    start_date: date = Field(
        description="Start date of the meal plan"
    )
    days: int = Field(
        default=7,
        ge=1,
        le=14,
        description="Number of days in the plan (1-14)"
    )
    preferences: PlanPreferencesSchema = Field(
        default_factory=PlanPreferencesSchema,
        description="User preferences for plan generation"
    )


class GeneratePlanResponse(BaseModel):
    """Response after starting plan generation."""
    task_id: str = Field(description="Task ID for tracking generation progress")
    message: str = Field(description="Status message")


class IngredientSchema(BaseModel):
    """Schema for a meal ingredient."""
    id: UUID
    food_id: Optional[UUID] = Field(
        default=None,
        description="Reference to food catalogue (null for custom ingredients)"
    )
    name: str = Field(description="Display name of the ingredient")
    amount_grams: float = Field(description="Amount in grams")
    unit_label: Optional[str] = Field(
        default=None,
        description="Display label for amount (e.g., '1 szklanka')"
    )
    kcal: Optional[float] = Field(default=None, description="Calories for the amount")
    protein: Optional[float] = Field(default=None, description="Protein in grams")
    fat: Optional[float] = Field(default=None, description="Fat in grams")
    carbs: Optional[float] = Field(default=None, description="Carbohydrates in grams")
    gi_per_100g: Optional[float] = Field(default=None, description="Glycemic index per 100g")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, orm_obj) -> "IngredientSchema":
        """Create schema from ORM model with custom name handling."""
        return cls(
            id=orm_obj.id,
            food_id=orm_obj.food_id,
            name=orm_obj.custom_name or "",
            amount_grams=orm_obj.amount_grams,
            unit_label=orm_obj.unit_label,
            kcal=orm_obj.kcal,
            protein=orm_obj.protein,
            fat=orm_obj.fat,
            carbs=orm_obj.carbs,
            gi_per_100g=getattr(orm_obj, 'gi_per_100g', None),
        )


class MealSchema(BaseModel):
    """Schema for a single meal within a day."""
    id: UUID
    meal_type: str = Field(
        description="Type of meal: breakfast, second_breakfast, lunch, snack, dinner"
    )
    name: str = Field(description="Name of the meal/recipe")
    description: Optional[str] = Field(
        default=None,
        description="Preparation instructions or description"
    )
    preparation_time_minutes: Optional[int] = Field(
        default=None,
        description="Estimated preparation time"
    )
    ingredients: List[IngredientSchema] = Field(
        default_factory=list,
        description="List of ingredients in this meal"
    )
    total_kcal: Optional[float] = Field(default=None, description="Total calories")
    total_protein: Optional[float] = Field(default=None, description="Total protein in grams")
    total_fat: Optional[float] = Field(default=None, description="Total fat in grams")
    total_carbs: Optional[float] = Field(default=None, description="Total carbs in grams")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, orm_obj) -> "MealSchema":
        """Create schema from ORM model."""
        return cls(
            id=orm_obj.id,
            meal_type=orm_obj.meal_type,
            name=orm_obj.name,
            description=orm_obj.description,
            preparation_time_minutes=orm_obj.preparation_time_minutes,
            ingredients=[
                IngredientSchema.from_orm_model(ing)
                for ing in orm_obj.ingredients
            ],
            total_kcal=orm_obj.total_kcal,
            total_protein=orm_obj.total_protein,
            total_fat=orm_obj.total_fat,
            total_carbs=orm_obj.total_carbs,
        )


class DaySchema(BaseModel):
    """Schema for a single day within a meal plan."""
    id: UUID
    day_number: int = Field(description="Day number within the plan (1-indexed)")
    day_date: Optional[date] = Field(
        default=None,
        alias="date",
        description="Calendar date for this day"
    )
    meals: List[MealSchema] = Field(
        default_factory=list,
        description="List of meals for this day"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @classmethod
    def from_orm_model(cls, orm_obj) -> "DaySchema":
        """Create schema from ORM model."""
        return cls(
            id=orm_obj.id,
            day_number=orm_obj.day_number,
            day_date=orm_obj.date,
            meals=[MealSchema.from_orm_model(meal) for meal in orm_obj.meals],
        )


class MealPlanSchema(BaseModel):
    """Full meal plan schema with all details."""
    id: UUID
    name: Optional[str] = Field(default=None, description="Name of the plan")
    start_date: date = Field(description="Start date of the plan")
    end_date: date = Field(description="End date of the plan")
    status: str = Field(description="Plan status: draft, active, archived")
    preferences: Optional[dict] = Field(
        default=None,
        description="Preferences used for generation"
    )
    daily_targets: Optional[dict] = Field(
        default=None,
        description="Calculated daily macro targets"
    )
    days: List[DaySchema] = Field(
        default_factory=list,
        description="List of days in the plan"
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, orm_obj) -> "MealPlanSchema":
        """Create schema from ORM model."""
        return cls(
            id=orm_obj.id,
            name=orm_obj.name,
            start_date=orm_obj.start_date,
            end_date=orm_obj.end_date,
            status=orm_obj.status,
            preferences=orm_obj.preferences,
            daily_targets=orm_obj.daily_targets,
            days=[DaySchema.from_orm_model(day) for day in orm_obj.days],
        )


class MealPlanSummarySchema(BaseModel):
    """Summary schema for listing meal plans (without nested data)."""
    id: UUID
    name: Optional[str] = Field(default=None, description="Name of the plan")
    start_date: date = Field(description="Start date of the plan")
    end_date: date = Field(description="End date of the plan")
    status: str = Field(description="Plan status: draft, active, archived")

    model_config = ConfigDict(from_attributes=True)


class MealPlanListResponse(BaseModel):
    """Response for listing meal plans."""
    plans: List[MealPlanSummarySchema] = Field(
        description="List of meal plan summaries"
    )


class DailyTargetsResponse(BaseModel):
    """Response for daily macro targets calculation."""
    kcal: int = Field(description="Target daily calories")
    protein: float = Field(description="Target daily protein in grams")
    fat: float = Field(description="Target daily fat in grams")
    carbs: float = Field(description="Target daily carbohydrates in grams")


class UpdatePlanStatusRequest(BaseModel):
    """Request body for updating plan status."""
    status: str = Field(
        description="New status: active or archived"
    )
