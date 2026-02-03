"""
Tests for VisionProcessingService.

Target: src/ai/application/vision_service.py
Mocks: VisionExtractor, PgVectorSearchService, get_embedding_service, PgVectorSearchAdapter
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.application.dto import ProcessedMealDTO
from src.ai.domain.models import (
    MealRecognitionResult,
    MatchedProduct,
    MealExtraction,
    ExtractedFoodItem,
    MealType,
)


def _make_matched_product(name="ryż biały", strategy="vision_vector_hybrid"):
    return MatchedProduct(
        product_id=str(uuid.uuid4()),
        name_pl=name,
        name_en="white rice",
        quantity_grams=200.0,
        kcal=130.0,
        protein=5.0,
        fat=0.5,
        carbs=28.0,
        match_confidence=0.9,
        unit_matched="g",
        quantity_unit_value=200.0,
        original_query="ryż",
        match_strategy=strategy,
    )


def _make_recognition_result(matched=None, unmatched=None):
    return MealRecognitionResult(
        matched_products=matched or [],
        unmatched_chunks=unmatched or [],
        overall_confidence=0.8 if matched else 0.0,
        processing_time_ms=50.0,
    )


def _make_extraction(items=None, meal_type=MealType.LUNCH):
    return MealExtraction(
        meal_type=meal_type,
        raw_transcription="[Analiza Obrazu]",
        items=items or [],
        overall_confidence=0.9,
    )


def _create_service():
    """Create VisionProcessingService with heavy imports patched."""
    with patch("src.ai.infrastructure.search.PgVectorSearchService") as mock_pvs, \
         patch("src.ai.infrastructure.embedding.get_embedding_service") as mock_ges, \
         patch("src.ai.application.vision_service.VisionExtractor") as mock_ve:
        mock_ges.return_value = MagicMock()
        mock_pvs.return_value = MagicMock()
        mock_ve_instance = MagicMock()
        mock_ve_instance.client = MagicMock()
        mock_ve_instance.extract_from_image = AsyncMock()
        mock_ve.return_value = mock_ve_instance

        from src.ai.application.vision_service import VisionProcessingService
        service = VisionProcessingService()

    return service, mock_ve_instance


# ============================================================================
# TestProcessImage
# ============================================================================


class TestProcessImage:
    @pytest.mark.asyncio
    async def test_raises_value_error_when_session_none(self):
        service, _ = _create_service()
        with pytest.raises(ValueError, match="Database session is required"):
            await service.process_image(b"image_data", session=None)

    @pytest.mark.asyncio
    async def test_happy_path(self):
        service, mock_extractor = _create_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(name="ryż", quantity_value=200.0, quantity_unit="g")
            ]),
            0.9,
        )

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_from_vision_items = AsyncMock(
            return_value=_make_recognition_result(matched=[_make_matched_product()])
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_image(b"image_data", MagicMock())

        assert isinstance(result, ProcessedMealDTO)
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_empty_extraction_returns_empty_items(self):
        service, mock_extractor = _create_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[]),
            0.0,
        )

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_from_vision_items = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_image(b"image_data", MagicMock())

        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_meal_type_from_extraction(self):
        service, mock_extractor = _create_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[], meal_type=MealType.BREAKFAST),
            0.9,
        )

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_from_vision_items = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_image(b"image_data", MagicMock())

        assert result.meal_type == "breakfast"

    @pytest.mark.asyncio
    async def test_processing_time_positive(self):
        service, mock_extractor = _create_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[]),
            0.0,
        )

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_from_vision_items = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_image(b"image_data", MagicMock())

        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_raw_transcription_is_image_analysis(self):
        service, mock_extractor = _create_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[]),
            0.0,
        )

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_from_vision_items = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_image(b"image_data", MagicMock())

        assert result.raw_transcription == "[Analiza Obrazu]"


# ============================================================================
# TestBuildDto
# ============================================================================


class TestBuildDto:
    def test_matched_strategy_produces_matched_status(self):
        service, _ = _create_service()
        result = _make_recognition_result(
            matched=[_make_matched_product(strategy="vision_vector_hybrid")]
        )
        dto = service._build_dto(result, MealType.LUNCH, 100.0)
        assert dto.items[0].status == "matched"

    def test_ai_estimate_strategy_produces_needs_confirmation(self):
        service, _ = _create_service()
        result = _make_recognition_result(
            matched=[_make_matched_product(strategy="vision_ai_estimate")]
        )
        dto = service._build_dto(result, MealType.LUNCH, 100.0)
        assert dto.items[0].status == "needs_confirmation"

    def test_unmatched_produces_not_found(self):
        service, _ = _create_service()
        result = _make_recognition_result(unmatched=["nieznany produkt"])
        dto = service._build_dto(result, MealType.SNACK, 50.0)
        assert dto.items[0].status == "not_found"
        assert dto.items[0].kcal == 0.0

    def test_meal_type_enum_to_string(self):
        service, _ = _create_service()
        result = _make_recognition_result()
        dto = service._build_dto(result, MealType.DINNER, 10.0)
        assert dto.meal_type == "dinner"

    def test_breakfast_meal_type(self):
        service, _ = _create_service()
        result = _make_recognition_result()
        dto = service._build_dto(result, MealType.BREAKFAST, 10.0)
        assert dto.meal_type == "breakfast"


# ============================================================================
# TestGetSystemStatus
# ============================================================================


class TestGetSystemStatus:
    def test_returns_dict_with_keys(self):
        service, _ = _create_service()
        status = service.get_system_status()
        assert "gemini_vision_available" in status
        assert "pgvector_service_ready" in status

    def test_gemini_unavailable_when_client_none(self):
        service, _ = _create_service()
        service.vision_extractor.client = None
        status = service.get_system_status()
        assert status["gemini_vision_available"] is False

    def test_gemini_available_when_client_present(self):
        service, _ = _create_service()
        service.vision_extractor.client = MagicMock()
        status = service.get_system_status()
        assert status["gemini_vision_available"] is True
