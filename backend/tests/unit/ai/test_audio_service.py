"""
Tests for AudioProcessingService.

Target: src/ai/application/audio_service.py
Mocks: STTPort, PgVectorSearchService, get_embedding_service, PgVectorSearchAdapter
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.application.dto import ProcessedMealDTO, ProcessedFoodItemDTO
from src.ai.domain.models import (
    MealRecognitionResult,
    MatchedProduct,
    IngredientChunk,
)
from src.ai.domain.exceptions import (
    AudioProcessingException,
    TranscriptionFailedException,
)


def _make_mock_stt():
    stt = MagicMock()
    stt.transcribe = AsyncMock(return_value="200g ryżu i pierś z kurczaka")
    stt.is_available = MagicMock(return_value=True)
    stt.load_model = AsyncMock()
    return stt


def _make_mock_nlu():
    nlu = MagicMock()
    nlu.normalize_text = MagicMock(side_effect=lambda x: x.lower())
    nlu.process_text = MagicMock(return_value=[
        IngredientChunk(original_text="ryż", text_for_search="ryż", quantity_value=200.0, quantity_unit="g"),
    ])
    nlu.verify_keyword_consistency = MagicMock(return_value=True)
    return nlu


def _make_mock_slm():
    slm = MagicMock()
    slm.is_available = MagicMock(return_value=False)
    return slm


def _create_service(stt=None, nlu=None, slm=None):
    """Create AudioProcessingService with all heavy imports patched."""
    mock_stt = stt or _make_mock_stt()
    mock_nlu = nlu or _make_mock_nlu()
    mock_slm = slm or _make_mock_slm()

    # Patch the imports that happen inside __init__ via the infrastructure package
    with patch("src.ai.infrastructure.search.PgVectorSearchService") as mock_pvs, \
         patch("src.ai.infrastructure.embedding.get_embedding_service") as mock_ges:
        mock_ges.return_value = MagicMock()
        mock_pvs.return_value = MagicMock()

        from src.ai.application.audio_service import AudioProcessingService
        service = AudioProcessingService(
            stt_client=mock_stt,
            nlu_processor=mock_nlu,
            slm_extractor=mock_slm,
        )
    return service


def _make_recognition_result(matched=None, unmatched=None):
    return MealRecognitionResult(
        matched_products=matched or [],
        unmatched_chunks=unmatched or [],
        overall_confidence=0.8 if matched else 0.0,
        processing_time_ms=50.0,
    )


def _make_matched_product(name="ryż biały", kcal=130.0):
    return MatchedProduct(
        product_id=str(uuid.uuid4()),
        name_pl=name,
        name_en="white rice",
        quantity_grams=200.0,
        kcal=kcal,
        protein=5.0,
        fat=0.5,
        carbs=28.0,
        match_confidence=0.9,
        unit_matched="g",
        quantity_unit_value=200.0,
        original_query="ryż",
        match_strategy="semantic_search",
    )


# ============================================================================
# TestProcessAudio
# ============================================================================


class TestProcessAudio:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_stt = _make_mock_stt()
        service = _create_service(stt=mock_stt)

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_meal = AsyncMock(
            return_value=_make_recognition_result(
                matched=[_make_matched_product()]
            )
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            mock_session = MagicMock()
            result = await service.process_audio(b"audio_data", session=mock_session)

        assert isinstance(result, ProcessedMealDTO)
        assert len(result.items) == 1
        assert result.items[0].status == "matched"

    @pytest.mark.asyncio
    async def test_raises_value_error_when_session_none(self):
        service = _create_service()
        with pytest.raises(ValueError, match="Database session is required"):
            await service.process_audio(b"audio_data", session=None)

    @pytest.mark.asyncio
    async def test_transcription_failed_reraised(self):
        mock_stt = _make_mock_stt()
        mock_stt.transcribe.side_effect = TranscriptionFailedException("STT failed")
        service = _create_service(stt=mock_stt)

        mock_meal_service = MagicMock()
        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            with pytest.raises(TranscriptionFailedException):
                await service.process_audio(b"audio_data", session=MagicMock())

    @pytest.mark.asyncio
    async def test_generic_exception_wrapped(self):
        mock_stt = _make_mock_stt()
        mock_stt.transcribe.side_effect = RuntimeError("Unexpected")
        service = _create_service(stt=mock_stt)

        mock_meal_service = MagicMock()
        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            with pytest.raises(AudioProcessingException):
                await service.process_audio(b"audio_data", session=MagicMock())

    @pytest.mark.asyncio
    async def test_correct_language_passed_to_stt(self):
        mock_stt = _make_mock_stt()
        service = _create_service(stt=mock_stt)

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_meal = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            await service.process_audio(b"data", language="en", session=MagicMock())

        mock_stt.transcribe.assert_called_once_with(b"data", language="en")

    @pytest.mark.asyncio
    async def test_processing_time_positive(self):
        mock_stt = _make_mock_stt()
        service = _create_service(stt=mock_stt)

        mock_meal_service = MagicMock()
        mock_meal_service.recognize_meal = AsyncMock(
            return_value=_make_recognition_result()
        )

        with patch.object(service, "_get_meal_service", return_value=mock_meal_service):
            result = await service.process_audio(b"data", session=MagicMock())

        assert result.processing_time_ms > 0


# ============================================================================
# TestBuildDto
# ============================================================================


class TestBuildDto:
    def test_matched_products_have_status_matched(self):
        service = _create_service()
        result = _make_recognition_result(matched=[_make_matched_product()])

        dto = service._build_dto(result, "200g ryżu", 100.0)
        assert dto.items[0].status == "matched"
        assert dto.items[0].name == "ryż biały"

    def test_unmatched_chunks_have_status_not_found(self):
        service = _create_service()
        result = _make_recognition_result(unmatched=["coś dziwnego"])

        dto = service._build_dto(result, "coś dziwnego", 50.0)
        assert dto.items[0].status == "not_found"
        assert dto.items[0].kcal == 0.0
        assert dto.items[0].quantity_grams == 100.0

    def test_units_included(self):
        service = _create_service()
        mp = _make_matched_product()
        mp.units = [{"label": "szklanka", "unit": "szklanka", "grams": 250.0}]
        result = _make_recognition_result(matched=[mp])

        dto = service._build_dto(result, "mleko", 30.0)
        assert len(dto.items[0].units) == 1

    def test_raw_transcription_preserved(self):
        service = _create_service()
        result = _make_recognition_result()
        dto = service._build_dto(result, "test transcription", 10.0)
        assert dto.raw_transcription == "test transcription"

    def test_processing_time_set(self):
        service = _create_service()
        result = _make_recognition_result()
        dto = service._build_dto(result, "test", 123.4)
        assert dto.processing_time_ms == 123.4


# ============================================================================
# TestDetectMealTypeSimple
# ============================================================================


class TestDetectMealTypeSimple:
    def test_sniadanie_returns_breakfast(self):
        service = _create_service()
        assert service._detect_meal_type_simple("na śniadanie jajka") == "breakfast"

    def test_obiad_returns_lunch(self):
        service = _create_service()
        assert service._detect_meal_type_simple("obiad z ziemniakami") == "lunch"

    def test_kolacja_returns_dinner(self):
        service = _create_service()
        assert service._detect_meal_type_simple("na kolację kanapka") == "dinner"

    def test_zupa_returns_lunch(self):
        service = _create_service()
        assert service._detect_meal_type_simple("zupa pomidorowa") == "lunch"

    def test_default_returns_snack(self):
        service = _create_service()
        assert service._detect_meal_type_simple("jabłko i banan") == "snack"

    def test_case_insensitive(self):
        service = _create_service()
        assert service._detect_meal_type_simple("ŚNIADANIE z serem") == "breakfast"


# ============================================================================
# TestTranscribeOnly
# ============================================================================


class TestTranscribeOnly:
    @pytest.mark.asyncio
    async def test_delegates_to_stt(self):
        mock_stt = _make_mock_stt()
        mock_stt.transcribe.return_value = "test transcription"
        service = _create_service(stt=mock_stt)

        result = await service.transcribe_only(b"audio", "pl")
        assert result == "test transcription"
        mock_stt.transcribe.assert_called_once_with(b"audio", "pl")


# ============================================================================
# TestGetSystemStatus
# ============================================================================


class TestGetSystemStatus:
    def test_returns_dict_with_all_keys(self):
        service = _create_service()
        status = service.get_system_status()
        assert "whisper_available" in status
        assert "slm_available" in status
        assert "search_mode" in status
        assert "pgvector_service_ready" in status

    def test_slm_available_false_when_none(self):
        service = _create_service()
        service.slm_extractor = None
        status = service.get_system_status()
        assert status["slm_available"] is False

    def test_slm_available_true_when_present(self):
        mock_slm = MagicMock()
        mock_slm.is_available.return_value = True
        service = _create_service(slm=mock_slm)
        status = service.get_system_status()
        assert status["slm_available"] is True

    def test_search_mode_is_pgvector(self):
        service = _create_service()
        status = service.get_system_status()
        assert status["search_mode"] == "pgvector"
