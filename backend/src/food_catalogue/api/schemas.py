import uuid
from typing import Optional, List

from pydantic import BaseModel


from src.food_catalogue.domain.enums import UnitType, UnitLabel


class UnitInfoSchema(BaseModel):
    unit: UnitType
    grams: float
    label: UnitLabel


class NutritionSchema(BaseModel):
    kcal_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float


class FoodOutSchema(BaseModel):
    id: Optional[uuid.UUID]
    name: str
    barcode: Optional[str] = None
    category: Optional[str] = None
    default_unit: str = "gram"
    units: Optional[List[UnitInfoSchema]] = None
    nutrition: NutritionSchema
    owner_id: Optional[uuid.UUID] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class CreateCustomFoodIn(BaseModel):
    name: str
    barcode: Optional[str] = None
    nutrition: NutritionSchema
