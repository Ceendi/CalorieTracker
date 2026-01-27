"""
SQLAlchemy ORM models for meal planning module.

Hierarchical structure:
    MealPlan -> MealPlanDay -> MealPlanMeal -> MealPlanIngredient
"""
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import UUIDModel


class MealPlanModel(UUIDModel):
    """
    A meal plan for a user spanning multiple days.

    Attributes:
        user_id: Owner of the meal plan
        name: Optional name for the plan
        start_date: First day of the plan
        end_date: Last day of the plan
        preferences: User preferences used for generation (JSONB)
        daily_targets: Calculated daily macro targets (JSONB)
        status: Plan status (draft, active, archived)
    """
    __tablename__ = "meal_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
    daily_targets: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    days: Mapped[List["MealPlanDayModel"]] = relationship(
        "MealPlanDayModel",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MealPlanDayModel.day_number"
    )


class MealPlanDayModel(UUIDModel):
    """
    A single day within a meal plan.

    Attributes:
        meal_plan_id: Parent meal plan
        day_number: Day number within the plan (1-indexed)
        date: Actual calendar date for this day
        notes: Optional notes for the day
    """
    __tablename__ = "meal_plan_days"

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("meal_plan_id", "day_number", name="uix_meal_plan_day_number"),
        CheckConstraint("day_number >= 1", name="check_day_number_positive"),
    )

    plan: Mapped["MealPlanModel"] = relationship("MealPlanModel", back_populates="days")
    meals: Mapped[List["MealPlanMealModel"]] = relationship(
        "MealPlanMealModel",
        back_populates="day",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MealPlanMealModel.sort_order"
    )


class MealPlanMealModel(UUIDModel):
    """
    A single meal within a day (e.g., breakfast, lunch, dinner).

    Attributes:
        meal_plan_day_id: Parent day
        meal_type: Type of meal (breakfast, second_breakfast, lunch, snack, dinner)
        name: Name of the meal/recipe
        description: Preparation instructions or description
        preparation_time_minutes: Estimated preparation time
        total_*: Aggregated nutritional values from ingredients
        sort_order: Order within the day
    """
    __tablename__ = "meal_plan_meals"

    meal_plan_day_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meal_plan_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preparation_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    total_kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_carbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    day: Mapped["MealPlanDayModel"] = relationship("MealPlanDayModel", back_populates="meals")
    ingredients: Mapped[List["MealPlanIngredientModel"]] = relationship(
        "MealPlanIngredientModel",
        back_populates="meal",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="MealPlanIngredientModel.sort_order"
    )


class MealPlanIngredientModel(UUIDModel):
    """
    A single ingredient within a meal.

    Attributes:
        meal_plan_meal_id: Parent meal
        food_id: Reference to food catalogue (optional - may be custom ingredient)
        custom_name: Name if not linked to food catalogue
        amount_grams: Amount in grams
        unit_label: Display label for amount (e.g., "1 cup", "2 slices")
        kcal, protein, fat, carbs: Calculated nutritional values for the amount
        sort_order: Order within the meal
    """
    __tablename__ = "meal_plan_ingredients"

    meal_plan_meal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meal_plan_meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    food_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    custom_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_grams: Mapped[float] = mapped_column(Float, nullable=False)
    unit_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    kcal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    meal: Mapped["MealPlanMealModel"] = relationship("MealPlanMealModel", back_populates="ingredients")
