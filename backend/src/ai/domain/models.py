from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from src.tracking.domain.entities import MealType

__all__ = [
    'MealType', 'ExtractionMethod', 'ExtractedFoodItem', 'MealExtraction',
    'SearchCandidate', 'MatchedProduct', 'IngredientChunk', 'MealRecognitionResult'
]


class ExtractionMethod(str, Enum):
    RULE_BASED = "rule_based"
    SEMANTIC_SEARCH = "semantic_search"
    SLM = "slm"


class ExtractedFoodItem(BaseModel):
    name: str
    quantity_value: float = 1.0
    quantity_unit: str = "porcja"
    confidence: float = 1.0
    extraction_method: Optional[ExtractionMethod] = None
    is_vague_quantity: bool = False
    meal_context: Optional[str] = None
    kcal: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None


class MealExtraction(BaseModel):
    meal_type: MealType
    raw_transcription: str
    items: List[ExtractedFoodItem]
    overall_confidence: float = 0.0


class SearchCandidate(BaseModel):
    product_id: str = Field(..., description="Product ID (string for UUID compatibility)")
    name: str = Field(..., description="Product name from the database")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    category: Optional[str] = Field(None, description="Product category for heuristic boosting")
    passed_guard: bool = Field(True, description="Whether it passed the keyword guard reranking")
    notes: Optional[str] = Field(None, description="Debug info about matching (e.g. vector score, heuristic penalties)")


class MatchedProduct(BaseModel):
    product_id: str = Field(..., description="Product ID (string for UUID compatibility)")
    name_pl: str
    name_en: str = ""
    quantity_grams: float = 0.0
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    match_confidence: float = Field(..., description="Final confidence score (0-1)")
    unit_matched: str = "g"
    quantity_unit_value: float = 1.0
    original_query: str = Field(..., description="The original user chunk text")
    match_strategy: str = Field("semantic_search")
    notes: str = ""
    units: List[dict] = Field(default_factory=list)
    alternatives: List[SearchCandidate] = Field(default_factory=list)

    @property
    def name(self) -> str:
        return self.name_pl

    @property
    def confidence(self) -> float:
        return self.match_confidence


class IngredientChunk(BaseModel):
    original_text: str = Field(..., description="Full text as extracted from the transcription")
    text_for_search: str = Field(..., description="Cleaned and normalized text used for semantic search")
    quantity_value: Optional[float] = Field(None, description="Extracted numeric quantity")
    quantity_unit: Optional[str] = Field(None, description="Extracted unit (e.g., g, ml, szt)")
    is_composite: bool = Field(False, description="Flag for composite dishes that expand to ingredients")


class MealRecognitionResult(BaseModel):
    matched_products: List[MatchedProduct]
    unmatched_chunks: List[str] = Field(default_factory=list)
    overall_confidence: float = 0.0
    processing_time_ms: float = 0.0
