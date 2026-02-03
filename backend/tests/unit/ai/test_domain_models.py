"""
Tests for AI domain models and DTOs.

Target: src/ai/domain/models.py, src/ai/application/dto.py
"""

import uuid

import pytest
from pydantic import ValidationError

from src.ai.domain.models import (
    SearchCandidate,
    MatchedProduct,
    IngredientChunk,
    ExtractedFoodItem,
    MealExtraction,
    MealRecognitionResult,
    MealType,
    ExtractionMethod,
)
from src.ai.application.dto import (
    ProcessedFoodItemDTO,
    ProcessedMealDTO,
    TranscriptionResultDTO,
)


# ============================================================================
# TestSearchCandidate
# ============================================================================


class TestSearchCandidate:
    def test_required_fields(self):
        c = SearchCandidate(product_id="abc-123", name="mleko", score=0.8)
        assert c.product_id == "abc-123"
        assert c.name == "mleko"
        assert c.score == 0.8

    def test_defaults(self):
        c = SearchCandidate(product_id="x", name="y", score=0.5)
        assert c.passed_guard is True
        assert c.notes is None
        assert c.category is None

    def test_optional_category(self):
        c = SearchCandidate(product_id="x", name="y", score=0.5, category="DAI")
        assert c.category == "DAI"

    def test_passed_guard_false(self):
        c = SearchCandidate(product_id="x", name="y", score=0.5, passed_guard=False)
        assert c.passed_guard is False


# ============================================================================
# TestMatchedProduct
# ============================================================================


class TestMatchedProduct:
    def test_name_property(self):
        mp = MatchedProduct(
            product_id="p1",
            name_pl="mleko 3.2%",
            match_confidence=0.9,
            original_query="mleko",
        )
        assert mp.name == "mleko 3.2%"

    def test_confidence_property(self):
        mp = MatchedProduct(
            product_id="p1",
            name_pl="mleko",
            match_confidence=0.75,
            original_query="mleko",
        )
        assert mp.confidence == 0.75

    def test_default_empty_lists(self):
        mp = MatchedProduct(
            product_id="p1",
            name_pl="mleko",
            match_confidence=0.8,
            original_query="mleko",
        )
        assert mp.units == []
        assert mp.alternatives == []

    def test_default_values(self):
        mp = MatchedProduct(
            product_id="p1",
            name_pl="mleko",
            match_confidence=0.8,
            original_query="mleko",
        )
        assert mp.name_en == ""
        assert mp.quantity_grams == 0.0
        assert mp.kcal == 0.0
        assert mp.unit_matched == "g"
        assert mp.match_strategy == "semantic_search"


# ============================================================================
# TestIngredientChunk
# ============================================================================


class TestIngredientChunk:
    def test_required_fields(self):
        chunk = IngredientChunk(
            original_text="200g ryżu",
            text_for_search="ryż",
        )
        assert chunk.original_text == "200g ryżu"
        assert chunk.text_for_search == "ryż"

    def test_defaults(self):
        chunk = IngredientChunk(original_text="ryż", text_for_search="ryż")
        assert chunk.quantity_value is None
        assert chunk.quantity_unit is None
        assert chunk.is_composite is False

    def test_with_quantity(self):
        chunk = IngredientChunk(
            original_text="200g ryżu",
            text_for_search="ryż",
            quantity_value=200.0,
            quantity_unit="g",
        )
        assert chunk.quantity_value == 200.0
        assert chunk.quantity_unit == "g"


# ============================================================================
# TestExtractedFoodItem
# ============================================================================


class TestExtractedFoodItem:
    def test_defaults(self):
        item = ExtractedFoodItem(name="ryż")
        assert item.quantity_value == 1.0
        assert item.quantity_unit == "porcja"
        assert item.confidence == 1.0

    def test_optional_macros_none(self):
        item = ExtractedFoodItem(name="ryż")
        assert item.kcal is None
        assert item.protein is None
        assert item.fat is None
        assert item.carbs is None

    def test_with_macros(self):
        item = ExtractedFoodItem(
            name="ryż", kcal=130.0, protein=2.7, fat=0.3, carbs=28.0
        )
        assert item.kcal == 130.0
        assert item.protein == 2.7

    def test_extraction_method(self):
        item = ExtractedFoodItem(
            name="test", extraction_method=ExtractionMethod.SLM
        )
        assert item.extraction_method == ExtractionMethod.SLM

    def test_extraction_method_values(self):
        assert ExtractionMethod.RULE_BASED.value == "rule_based"
        assert ExtractionMethod.SEMANTIC_SEARCH.value == "semantic_search"
        assert ExtractionMethod.SLM.value == "slm"


# ============================================================================
# TestProcessedFoodItemDTO
# ============================================================================


class TestProcessedFoodItemDTO:
    def test_valid_status_matched(self):
        dto = ProcessedFoodItemDTO(
            product_id=uuid.uuid4(),
            name="ryż",
            quantity_grams=200.0,
            kcal=260.0,
            protein=5.0,
            fat=0.5,
            carbs=56.0,
            confidence=0.9,
            unit_matched="g",
            quantity_unit_value=200.0,
            status="matched",
        )
        assert dto.status == "matched"

    def test_valid_status_not_found(self):
        dto = ProcessedFoodItemDTO(
            name="unknown",
            quantity_grams=100.0,
            kcal=0.0,
            protein=0.0,
            fat=0.0,
            carbs=0.0,
            confidence=0.0,
            unit_matched="porcja",
            quantity_unit_value=1.0,
            status="not_found",
        )
        assert dto.status == "not_found"

    def test_valid_status_needs_confirmation(self):
        dto = ProcessedFoodItemDTO(
            name="coś",
            quantity_grams=100.0,
            kcal=50.0,
            protein=2.0,
            fat=1.0,
            carbs=8.0,
            confidence=0.5,
            unit_matched="g",
            quantity_unit_value=100.0,
            status="needs_confirmation",
        )
        assert dto.status == "needs_confirmation"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            ProcessedFoodItemDTO(
                name="x",
                quantity_grams=1.0,
                kcal=0.0,
                protein=0.0,
                fat=0.0,
                carbs=0.0,
                confidence=0.5,
                unit_matched="g",
                quantity_unit_value=1.0,
                status="invalid_status",
            )

    def test_confidence_range_max(self):
        dto = ProcessedFoodItemDTO(
            name="x",
            quantity_grams=1.0,
            kcal=0.0,
            protein=0.0,
            fat=0.0,
            carbs=0.0,
            confidence=1.0,
            unit_matched="g",
            quantity_unit_value=1.0,
            status="matched",
        )
        assert dto.confidence == 1.0

    def test_confidence_range_min(self):
        dto = ProcessedFoodItemDTO(
            name="x",
            quantity_grams=1.0,
            kcal=0.0,
            protein=0.0,
            fat=0.0,
            carbs=0.0,
            confidence=0.0,
            unit_matched="g",
            quantity_unit_value=1.0,
            status="not_found",
        )
        assert dto.confidence == 0.0

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            ProcessedFoodItemDTO(
                name="x",
                quantity_grams=1.0,
                kcal=0.0,
                protein=0.0,
                fat=0.0,
                carbs=0.0,
                confidence=1.5,
                unit_matched="g",
                quantity_unit_value=1.0,
                status="matched",
            )


# ============================================================================
# TestProcessedMealDTO
# ============================================================================


class TestProcessedMealDTO:
    def test_all_fields(self):
        dto = ProcessedMealDTO(
            meal_type="lunch",
            items=[],
            raw_transcription="test text",
            processing_time_ms=150.0,
        )
        assert dto.meal_type == "lunch"
        assert dto.items == []
        assert dto.raw_transcription == "test text"
        assert dto.processing_time_ms == 150.0

    def test_default_processing_time(self):
        dto = ProcessedMealDTO(
            meal_type="snack",
            items=[],
            raw_transcription="test",
        )
        assert dto.processing_time_ms == 0.0


# ============================================================================
# TestMealExtraction
# ============================================================================


class TestMealExtraction:
    def test_all_fields(self):
        extraction = MealExtraction(
            meal_type=MealType.BREAKFAST,
            raw_transcription="jajka na śniadanie",
            items=[ExtractedFoodItem(name="jajko")],
            overall_confidence=0.8,
        )
        assert extraction.meal_type == MealType.BREAKFAST
        assert len(extraction.items) == 1

    def test_default_confidence(self):
        extraction = MealExtraction(
            meal_type=MealType.SNACK,
            raw_transcription="test",
            items=[],
        )
        assert extraction.overall_confidence == 0.0


# ============================================================================
# TestMealRecognitionResult
# ============================================================================


class TestMealRecognitionResult:
    def test_all_fields(self):
        result = MealRecognitionResult(
            matched_products=[],
            unmatched_chunks=["unknown"],
            overall_confidence=0.5,
            processing_time_ms=100.0,
        )
        assert result.unmatched_chunks == ["unknown"]
        assert result.processing_time_ms == 100.0

    def test_defaults(self):
        result = MealRecognitionResult(matched_products=[])
        assert result.unmatched_chunks == []
        assert result.overall_confidence == 0.0
        assert result.processing_time_ms == 0.0


# ============================================================================
# TestTranscriptionResultDTO
# ============================================================================


class TestTranscriptionResultDTO:
    def test_fields(self):
        dto = TranscriptionResultDTO(text="test transcription", language="pl")
        assert dto.text == "test transcription"
        assert dto.language == "pl"
