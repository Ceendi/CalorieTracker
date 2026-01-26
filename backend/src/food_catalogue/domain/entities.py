import uuid
from dataclasses import dataclass, field
from typing import Optional, List


from src.food_catalogue.domain.enums import UnitType, UnitLabel


@dataclass(frozen=True)
class UnitInfo:
    unit: UnitType    # "piece", "tablespoon", "teaspoon", "cup", "gram"
    grams: float      # how many grams is 1 unit
    label: UnitLabel  # display label, e.g. "sztuka (średnia)", "łyżka stołowa"


@dataclass(frozen=True)
class Nutrition:
    kcal_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float

    def __post_init__(self):
        if self.kcal_per_100g < 0:
            raise ValueError("kcal_per_100g cannot be negative")
        if self.protein_per_100g < 0:
            raise ValueError("protein_per_100g cannot be negative")
        if self.fat_per_100g < 0:
            raise ValueError("fat_per_100g cannot be negative")
        if self.carbs_per_100g < 0:
            raise ValueError("carbs_per_100g cannot be negative")


@dataclass
class Food:
    id: Optional[uuid.UUID]
    name: str
    barcode: Optional[str]
    nutrition: Nutrition
    category: Optional[str] = None
    default_unit: str = "gram"
    units: Optional[List[UnitInfo]] = field(default_factory=list)
    owner_id: Optional[uuid.UUID] = None
    source: Optional[str] = None  # 'public', 'base_db', 'openfoodfacts', 'user'

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty")
