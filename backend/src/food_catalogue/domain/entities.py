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
    category: Optional[str] = None
    default_unit: str = "gram"
    units: Optional[List[UnitInfo]] = field(default_factory=list)
    owner_id: Optional[uuid.UUID] = None
    source: Optional[str] = None  # 'public', 'base_db', 'openfoodfacts', 'user'
