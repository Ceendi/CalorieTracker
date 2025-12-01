import uuid
from typing import Optional

from pydantic import BaseModel


class NutritionSchema(BaseModel):
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float


class FoodOutSchema(BaseModel):
    id: Optional[uuid.UUID]
    name: str
    barcode: Optional[str] = None
    nutrition: NutritionSchema
    owner_id: Optional[uuid.UUID] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class CreateCustomFoodIn(BaseModel):
    name: str
    barcode: Optional[str] = None
    nutrition: NutritionSchema
