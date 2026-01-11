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
    prot_per_100g: float
    fat_per_100g: float
    carb_per_100g: float

    product_id: Optional[UUID] = None

    @property
    def computed_kcal(self) -> int:
        return int((self.amount_grams / 100) * self.kcal_per_100g)

    @property
    def computed_protein(self) -> float:
        return (self.amount_grams / 100) * self.prot_per_100g

    @property
    def computed_fat(self) -> float:
        return (self.amount_grams / 100) * self.fat_per_100g

    @property
    def computed_carbs(self) -> float:
        return (self.amount_grams / 100) * self.carb_per_100g


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
