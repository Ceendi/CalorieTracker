from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional
from uuid import UUID


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


@dataclass
class MealEntry:
    id: UUID
    daily_log_id: UUID
    meal_type: MealType
    product_name: str
    amount_grams: float

    kcal_per_100g: int
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float

    product_id: Optional[UUID] = None

    unit_label: Optional[str] = None
    unit_grams: Optional[float] = None
    unit_quantity: Optional[float] = None

    def __post_init__(self):
        if self.amount_grams < 0:
            raise ValueError("amount_grams cannot be negative")
        if self.kcal_per_100g < 0:
            raise ValueError("kcal_per_100g cannot be negative")
        if self.protein_per_100g < 0:
            raise ValueError("protein_per_100g cannot be negative")
        if self.fat_per_100g < 0:
            raise ValueError("fat_per_100g cannot be negative")
        if self.carbs_per_100g < 0:
            raise ValueError("carbs_per_100g cannot be negative")
        if not self.product_name or not self.product_name.strip():
            raise ValueError("product_name cannot be empty")

    @property
    def computed_kcal(self) -> int:
        return int((self.amount_grams / 100) * self.kcal_per_100g)

    @property
    def computed_protein(self) -> float:
        return (self.amount_grams / 100) * self.protein_per_100g

    @property
    def computed_fat(self) -> float:
        return (self.amount_grams / 100) * self.fat_per_100g

    @property
    def computed_carbs(self) -> float:
        return (self.amount_grams / 100) * self.carbs_per_100g


@dataclass
class DailyLog:
    id: UUID
    user_id: UUID
    date: date
    entries: List[MealEntry] = field(default_factory=list)

    @property
    def total_kcal(self) -> int:
        return sum(e.computed_kcal for e in self.entries)

    @property
    def total_protein(self) -> float:
        return sum(e.computed_protein for e in self.entries)

    @property
    def total_fat(self) -> float:
        return sum(e.computed_fat for e in self.entries)

    @property
    def total_carbs(self) -> float:
        return sum(e.computed_carbs for e in self.entries)
