import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Nutrition:
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float


@dataclass
class Food:
    id: Optional[uuid.UUID]
    name: str
    barcode: Optional[str]
    nutrition: Nutrition
    owner_id: Optional[uuid.UUID] = None
    source: Optional[str] = None  # 'public', 'external', 'user'
