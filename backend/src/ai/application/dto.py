import uuid
from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class ProcessedFoodItemDTO(BaseModel):
    product_id: Optional[uuid.UUID] = Field(None, description="ID of matched product")
    name: str = Field(description="Product name")
    quantity_grams: float = Field(description="Quantity in grams")
    kcal: float = Field(description="Calories")
    protein: float = Field(description="Protein in grams")
    fat: float = Field(description="Fat in grams")
    carbs: float = Field(description="Carbohydrates in grams")
    confidence: float = Field(ge=0.0, le=1.0, description="Match confidence")
    unit_matched: str = Field(description="Unit that was matched")
    quantity_unit_value: float = Field(1.0, description="Numeric value of the matched unit")
    status: Literal["matched", "not_found", "needs_confirmation"] = Field(description="Match status")
    units: List[dict] = Field(default_factory=list, description="Available product units")
    notes: Optional[str] = Field(None, description="Additional notes")
    glycemic_index: Optional[float] = Field(None, description="Glycemic index per 100g")


class ProcessedMealDTO(BaseModel):
    meal_type: str = Field(description="Type of meal")
    items: List[ProcessedFoodItemDTO] = Field(description="Processed food items")
    raw_transcription: str = Field(description="Original transcribed text")
    processing_time_ms: float = Field(default=0.0, description="Processing time in ms")


class TranscriptionResultDTO(BaseModel):
    text: str = Field(description="Transcribed text")
    language: str = Field(description="Detected/used language")
