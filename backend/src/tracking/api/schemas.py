from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.tracking.domain.entities import MealType


class MealEntryBase(BaseModel):
    product_id: UUID
    amount_grams: float
    unit_label: Optional[str] = None
    unit_grams: Optional[float] = None
    unit_quantity: Optional[float] = None


class MealEntryCreate(MealEntryBase):
    date: date
    meal_type: MealType


class MealBulkCreate(BaseModel):
    date: date
    meal_type: MealType
    items: List[MealEntryBase]


class MealEntryUpdate(BaseModel):
    amount_grams: Optional[float] = None
    meal_type: Optional[MealType] = None


class MealEntryRead(BaseModel):
    id: UUID
    daily_log_id: UUID
    product_id: Optional[UUID] = None
    meal_type: MealType
    product_name: str
    amount_grams: float
    computed_kcal: int
    computed_protein: float
    computed_fat: float
    computed_carbs: float

    kcal_per_100g: Optional[int] = None
    protein_per_100g: Optional[float] = None
    fat_per_100g: Optional[float] = None
    carbs_per_100g: Optional[float] = None

    unit_label: Optional[str] = None
    unit_grams: Optional[float] = None
    unit_quantity: Optional[float] = None
    gi_per_100g: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DailyLogRead(BaseModel):
    id: UUID
    date: date
    total_kcal: int
    total_protein: float
    total_fat: float
    total_carbs: float
    entries: List[MealEntryRead]

    model_config = ConfigDict(from_attributes=True)
