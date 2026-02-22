"""
Repository for meal planning module.

Handles all database operations for meal plans, including
mapping between ORM models and domain entities.
"""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.meal_planning.application.ports import MealPlanRepositoryPort
from src.meal_planning.domain.entities import (
    GeneratedPlan,
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
)
from src.meal_planning.infrastructure.orm_models import (
    MealPlanModel,
    MealPlanDayModel,
    MealPlanMealModel,
    MealPlanIngredientModel,
)


class MealPlanRepository(MealPlanRepositoryPort):
    """
    Repository for meal plan persistence.

    Handles CRUD operations for meal plans and provides
    mapping between domain entities and ORM models.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(
        self,
        user_id: UUID,
        plan: GeneratedPlan,
        name: str,
        start_date: date
    ) -> UUID:
        """
        Save a generated plan to the database.

        Maps the domain GeneratedPlan to ORM models and persists
        the entire plan hierarchy.

        Args:
            user_id: Owner of the plan
            plan: Generated plan to save
            name: Name for the plan
            start_date: Start date of the plan

        Returns:
            UUID of the created plan
        """
        end_date = start_date + timedelta(days=len(plan.days) - 1)

        db_plan = MealPlanModel(
            user_id=user_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            preferences=plan.preferences_applied,
            daily_targets=plan.generation_metadata.get("daily_targets", {}),
            status="draft"
        )

        for day in plan.days:
            db_day = MealPlanDayModel(
                day_number=day.day_number,
                date=start_date + timedelta(days=day.day_number - 1)
            )

            for idx, meal in enumerate(day.meals):
                db_meal = MealPlanMealModel(
                    meal_type=meal.meal_type,
                    name=meal.name,
                    description=meal.description,
                    preparation_time_minutes=meal.preparation_time_minutes,
                    total_kcal=meal.total_kcal,
                    total_protein=meal.total_protein,
                    total_fat=meal.total_fat,
                    total_carbs=meal.total_carbs,
                    sort_order=idx
                )

                for ing_idx, ing in enumerate(meal.ingredients):
                    db_ingredient = MealPlanIngredientModel(
                        food_id=ing.food_id,
                        # Always save the name to ensure it's available for display
                        # without requiring a join on the foods table
                        custom_name=ing.name,
                        amount_grams=ing.amount_grams,
                        unit_label=ing.unit_label,
                        kcal=ing.kcal,
                        protein=ing.protein,
                        fat=ing.fat,
                        carbs=ing.carbs,
                        gi_per_100g=ing.gi_per_100g,
                        sort_order=ing_idx
                    )
                    db_meal.ingredients.append(db_ingredient)

                db_day.meals.append(db_meal)

            db_plan.days.append(db_day)

        self.db.add(db_plan)
        await self.db.flush()
        return db_plan.id

    async def get_plan(self, plan_id: UUID) -> Optional[MealPlanModel]:
        """
        Get a plan with all nested relations.

        Uses selectinload for efficient eager loading of the
        entire plan hierarchy.

        Args:
            plan_id: ID of the plan to retrieve

        Returns:
            MealPlanModel with all relations loaded, or None if not found
        """
        stmt = (
            select(MealPlanModel)
            .options(
                selectinload(MealPlanModel.days)
                .selectinload(MealPlanDayModel.meals)
                .selectinload(MealPlanMealModel.ingredients)
            )
            .where(MealPlanModel.id == plan_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_plans(
        self,
        user_id: UUID,
        status: Optional[str] = None
    ) -> List[MealPlanModel]:
        """
        List user's meal plans.

        Returns plans ordered by creation date (newest first).
        Can be filtered by status.

        Args:
            user_id: Owner of the plans
            status: Optional status filter

        Returns:
            List of MealPlanModel (without nested relations)
        """
        stmt = select(MealPlanModel).where(MealPlanModel.user_id == user_id)
        if status:
            stmt = stmt.where(MealPlanModel.status == status)
        stmt = stmt.order_by(MealPlanModel.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_plan(self, plan_id: UUID) -> bool:
        """
        Delete a meal plan.

        Cascade delete removes all related days, meals, and ingredients.

        Args:
            plan_id: ID of the plan to delete

        Returns:
            True if plan was deleted, False if not found
        """
        plan = await self.get_plan(plan_id)
        if plan:
            await self.db.delete(plan)
            await self.db.flush()
            return True
        return False

    async def update_status(self, plan_id: UUID, status: str) -> bool:
        """
        Update the status of a meal plan.

        Args:
            plan_id: ID of the plan to update
            status: New status value

        Returns:
            True if plan was updated, False if not found
        """
        stmt = select(MealPlanModel).where(MealPlanModel.id == plan_id)
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()
        if plan:
            plan.status = status
            await self.db.flush()
            return True
        return False

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.db.commit()

    def to_domain_plan(self, orm_plan: MealPlanModel) -> GeneratedPlan:
        """
        Map ORM MealPlanModel to domain GeneratedPlan.

        Useful when you need to work with domain entities
        after loading from the database.

        Args:
            orm_plan: ORM model with all relations loaded

        Returns:
            Domain GeneratedPlan entity
        """
        days = []
        for orm_day in orm_plan.days:
            meals = []
            for orm_meal in orm_day.meals:
                ingredients = []
                for orm_ing in orm_meal.ingredients:
                    ingredients.append(GeneratedIngredient(
                        food_id=orm_ing.food_id,
                        name=orm_ing.custom_name or "",
                        amount_grams=orm_ing.amount_grams,
                        unit_label=orm_ing.unit_label,
                        kcal=orm_ing.kcal or 0.0,
                        protein=orm_ing.protein or 0.0,
                        fat=orm_ing.fat or 0.0,
                        carbs=orm_ing.carbs or 0.0,
                        gi_per_100g=orm_ing.gi_per_100g,
                    ))
                meals.append(GeneratedMeal(
                    meal_type=orm_meal.meal_type,
                    name=orm_meal.name,
                    description=orm_meal.description or "",
                    preparation_time_minutes=orm_meal.preparation_time_minutes or 0,
                    ingredients=ingredients,
                    total_kcal=orm_meal.total_kcal or 0.0,
                    total_protein=orm_meal.total_protein or 0.0,
                    total_fat=orm_meal.total_fat or 0.0,
                    total_carbs=orm_meal.total_carbs or 0.0,
                ))
            days.append(GeneratedDay(
                day_number=orm_day.day_number,
                meals=meals,
            ))

        return GeneratedPlan(
            days=days,
            preferences_applied=orm_plan.preferences or {},
            generation_metadata={"daily_targets": orm_plan.daily_targets or {}},
        )
