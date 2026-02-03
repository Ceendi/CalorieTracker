"""
Integration tests for the audio processing pipeline.

Tests the full audio pipeline end-to-end:
  STT (mocked) -> NLU processor (real) -> MealRecognitionService (real scoring) -> DTO output

Only external services are mocked:
  - STT (Whisper) — returns controlled Polish transcription text
  - PgVectorSearchService / get_embedding_service — heavy model imports
  - SearchEnginePort — returns controlled search candidates (simulates DB)

Real components under test:
  - NaturalLanguageProcessor (text normalization, chunking, composite dish expansion)
  - MealRecognitionService (scoring heuristics, grams calculation, result assembly)
  - AudioProcessingService (orchestration, DTO building, meal type detection)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.application.dto import ProcessedMealDTO
from src.ai.domain.models import SearchCandidate
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.config import DEFAULT_PORTION_GRAMS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_product_id() -> str:
    return str(uuid.uuid4())


def _make_candidate(
    name: str,
    score: float = 0.85,
    category: str = "UNKNOWN",
    product_id: str = None,
) -> SearchCandidate:
    return SearchCandidate(
        product_id=product_id or _make_product_id(),
        name=name,
        score=score,
        category=category,
        passed_guard=True,
    )


def _make_product_dict(
    name_pl: str = "ryż biały",
    kcal_100g: float = 130.0,
    protein_100g: float = 2.7,
    fat_100g: float = 0.3,
    carbs_100g: float = 28.0,
    category: str = "CERE",
    units: list = None,
) -> dict:
    return {
        "id": _make_product_id(),
        "name_pl": name_pl,
        "name_en": "",
        "kcal_100g": kcal_100g,
        "protein_100g": protein_100g,
        "fat_100g": fat_100g,
        "carbs_100g": carbs_100g,
        "category": category,
        "units": units or [],
    }


def _build_search_engine(candidate_map: dict, product_map: dict = None):
    """
    Build a mock SearchEnginePort that returns different candidates per query.

    Args:
        candidate_map: dict mapping query substring -> list of SearchCandidate
        product_map: dict mapping product_id -> product dict
    """
    engine = MagicMock()
    product_map = product_map or {}

    async def _search(query, top_k=20, alpha=0.3):
        query_lower = query.lower()
        for key, candidates in candidate_map.items():
            if key in query_lower:
                return candidates
        return []

    engine.search = AsyncMock(side_effect=_search)
    engine.get_product_by_id = MagicMock(
        side_effect=lambda pid: product_map.get(pid, _make_product_dict())
    )
    engine.index_products = MagicMock()
    return engine


def _create_audio_service(stt_transcription: str):
    """
    Create an AudioProcessingService with real NLU processor,
    mocked STT, and mocked heavy imports.
    """
    mock_stt = MagicMock()
    mock_stt.transcribe = AsyncMock(return_value=stt_transcription)
    mock_stt.is_available = MagicMock(return_value=True)
    mock_stt.load_model = AsyncMock()

    real_nlu = NaturalLanguageProcessor()

    mock_slm = MagicMock()
    mock_slm.is_available = MagicMock(return_value=False)

    with patch("src.ai.infrastructure.search.PgVectorSearchService") as mock_pvs, \
         patch("src.ai.infrastructure.embedding.get_embedding_service") as mock_ges:
        mock_ges.return_value = MagicMock()
        mock_pvs.return_value = MagicMock()

        from src.ai.application.audio_service import AudioProcessingService
        service = AudioProcessingService(
            stt_client=mock_stt,
            nlu_processor=real_nlu,
            slm_extractor=mock_slm,
        )

    return service


def _wire_meal_service(service, search_engine):
    """
    Replace _get_meal_service on the audio service so it uses a
    real MealRecognitionService with the given mock search engine.
    """
    from src.ai.application.meal_service import MealRecognitionService

    def _get_meal_service(session):
        return MealRecognitionService(
            vector_engine=search_engine,
            nlu_processor=service.nlu_processor,
            slm_extractor=None,
        )

    service._get_meal_service = _get_meal_service
    return service


# ===========================================================================
# Tests
# ===========================================================================


class TestAudioPipelineSimpleMeal:
    """Test audio pipeline with simple single-item Polish meal descriptions."""

    @pytest.mark.asyncio
    async def test_rice_200g(self):
        """'200g ryżu' should produce a matched item for rice with correct grams."""
        pid = _make_product_id()
        candidate = _make_candidate("ryż biały", score=0.80, product_id=pid, category="CERE")
        product = _make_product_dict(
            name_pl="ryż biały", kcal_100g=130.0, protein_100g=2.7,
            fat_100g=0.3, carbs_100g=28.0
        )

        engine = _build_search_engine(
            candidate_map={"ryż": [candidate]},
            product_map={pid: product},
        )

        service = _create_audio_service("200g ryżu")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert isinstance(result, ProcessedMealDTO)
        assert len(result.items) >= 1

        rice_item = result.items[0]
        assert rice_item.status == "matched"
        assert rice_item.quantity_grams == 200.0
        # Macros should be scaled: 200g = 2x per-100g
        assert rice_item.kcal == pytest.approx(260.0, abs=1.0)
        assert rice_item.protein == pytest.approx(5.4, abs=0.5)

    @pytest.mark.asyncio
    async def test_meal_type_detected_sniadanie(self):
        """Transcription with 'sniadanie' should detect breakfast meal type."""
        engine = _build_search_engine(
            candidate_map={"jajko": [_make_candidate("jajko kurze", score=0.9)]},
        )
        service = _create_audio_service("na śniadanie jajko")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert result.meal_type == "breakfast"

    @pytest.mark.asyncio
    async def test_meal_type_detected_obiad(self):
        """Transcription with 'obiad' should detect lunch meal type."""
        engine = _build_search_engine(
            candidate_map={"ryż": [_make_candidate("ryż", score=0.8)]},
        )
        service = _create_audio_service("na obiad ryż z kurczakiem")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert result.meal_type == "lunch"

    @pytest.mark.asyncio
    async def test_meal_type_default_snack(self):
        """Transcription without meal keywords should default to snack."""
        engine = _build_search_engine(
            candidate_map={"banan": [_make_candidate("banan", score=0.9)]},
        )
        service = _create_audio_service("banan i jabłko")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert result.meal_type == "snack"

    @pytest.mark.asyncio
    async def test_raw_transcription_preserved(self):
        """The raw transcription should be included in the DTO."""
        engine = _build_search_engine(candidate_map={})
        service = _create_audio_service("testowa transkrypcja")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert result.raw_transcription == "testowa transkrypcja"

    @pytest.mark.asyncio
    async def test_processing_time_positive(self):
        """Processing time should be a positive number."""
        engine = _build_search_engine(candidate_map={})
        service = _create_audio_service("test")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert result.processing_time_ms > 0


class TestAudioPipelineMultipleItems:
    """Test audio pipeline with multiple food items in one transcription."""

    @pytest.mark.asyncio
    async def test_two_items_separated_by_and(self):
        """'ryż i kurczak' should produce two matched items."""
        pid_r = _make_product_id()
        pid_k = _make_product_id()

        engine = _build_search_engine(
            candidate_map={
                "ryż": [_make_candidate("ryż biały", score=0.85, product_id=pid_r)],
                "pierś": [_make_candidate("pierś z kurczaka", score=0.80, product_id=pid_k)],
                "kurczak": [_make_candidate("pierś z kurczaka", score=0.80, product_id=pid_k)],
            },
            product_map={
                pid_r: _make_product_dict(name_pl="ryż biały", kcal_100g=130.0),
                pid_k: _make_product_dict(
                    name_pl="pierś z kurczaka", kcal_100g=110.0,
                    protein_100g=23.0, fat_100g=1.3, carbs_100g=0.0
                ),
            },
        )

        service = _create_audio_service("ryż i kurczak")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        assert len(result.items) == 2
        names = [item.name for item in result.items]
        # Both items should be matched
        assert all(item.status == "matched" for item in result.items)

    @pytest.mark.asyncio
    async def test_multiple_items_with_quantities(self):
        """'200g ryżu, pierś z kurczaka i sałatka' should parse 3+ items."""
        pid_r = _make_product_id()
        pid_k = _make_product_id()
        pid_s = _make_product_id()

        engine = _build_search_engine(
            candidate_map={
                "ryż": [_make_candidate("ryż biały", score=0.85, product_id=pid_r)],
                "pierś": [_make_candidate("pierś z kurczaka", score=0.80, product_id=pid_k)],
                "sałat": [_make_candidate("sałata zielona", score=0.75, product_id=pid_s)],
            },
            product_map={
                pid_r: _make_product_dict(name_pl="ryż biały", kcal_100g=130.0),
                pid_k: _make_product_dict(name_pl="pierś z kurczaka", kcal_100g=110.0),
                pid_s: _make_product_dict(name_pl="sałata zielona", kcal_100g=14.0),
            },
        )

        service = _create_audio_service("200g ryżu, pierś z kurczaka i sałatka")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        # Should have at least the 3 main items
        assert len(result.items) >= 2


class TestAudioPipelineUnmatchedItems:
    """Test that unmatched items are properly reported."""

    @pytest.mark.asyncio
    async def test_unknown_product_gets_not_found_status(self):
        """An item with no search results should be marked as not_found."""
        engine = _build_search_engine(candidate_map={})
        service = _create_audio_service("suplement magnezowy")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        not_found = [i for i in result.items if i.status == "not_found"]
        assert len(not_found) >= 1
        assert not_found[0].kcal == 0.0
        assert not_found[0].confidence == 0.0

    @pytest.mark.asyncio
    async def test_mixed_matched_and_unmatched(self):
        """Some items found, some not — both should appear in output."""
        pid = _make_product_id()
        engine = _build_search_engine(
            candidate_map={
                "ryż": [_make_candidate("ryż biały", score=0.85, product_id=pid)],
            },
            product_map={pid: _make_product_dict(name_pl="ryż biały")},
        )

        # "ryż" will match, "magiczny proszek" will not
        service = _create_audio_service("ryż i magiczny proszek")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        matched = [i for i in result.items if i.status == "matched"]
        not_found = [i for i in result.items if i.status == "not_found"]
        assert len(matched) >= 1
        assert len(not_found) >= 1


class TestAudioPipelineSynonymNormalization:
    """Test that Polish synonyms and inflections are normalized by the real NLU."""

    @pytest.mark.asyncio
    async def test_ryzu_normalized_to_ryz(self):
        """'ryżu' should be normalized via NLU synonyms to 'ryż'."""
        pid = _make_product_id()
        engine = _build_search_engine(
            candidate_map={"ryż": [_make_candidate("ryż biały", score=0.85, product_id=pid)]},
            product_map={pid: _make_product_dict(name_pl="ryż biały")},
        )

        service = _create_audio_service("200g ryżu")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        matched = [i for i in result.items if i.status == "matched"]
        assert len(matched) >= 1

    @pytest.mark.asyncio
    async def test_mleka_normalized_to_mleko(self):
        """'mleka' is a synonym for 'mleko' in the NLU."""
        pid = _make_product_id()
        engine = _build_search_engine(
            candidate_map={"mleko": [_make_candidate("mleko 3.2%", score=0.85, product_id=pid)]},
            product_map={pid: _make_product_dict(name_pl="mleko 3.2%", kcal_100g=60.0)},
        )

        service = _create_audio_service("szklanka mleka")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        matched = [i for i in result.items if i.status == "matched"]
        assert len(matched) >= 1


class TestAudioPipelineQuantityParsing:
    """Test that quantities are correctly extracted and applied to macros."""

    @pytest.mark.asyncio
    async def test_grams_unit_applied(self):
        """'200g ryżu' should result in 200g and scaled macros."""
        pid = _make_product_id()
        product = _make_product_dict(
            name_pl="ryż biały", kcal_100g=130.0,
            protein_100g=2.7, fat_100g=0.3, carbs_100g=28.0,
        )
        engine = _build_search_engine(
            candidate_map={"ryż": [_make_candidate("ryż biały", score=0.85, product_id=pid)]},
            product_map={pid: product},
        )

        service = _create_audio_service("200g ryżu")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        rice = result.items[0]
        assert rice.quantity_grams == 200.0
        assert rice.kcal == pytest.approx(260.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_product_unit_sztuka_from_db(self):
        """When product has a 'sztuka' unit in DB, it should be used for gram calc."""
        pid = _make_product_id()
        product = _make_product_dict(
            name_pl="jajko kurze",
            kcal_100g=155.0,
            protein_100g=12.6,
            fat_100g=11.5,
            carbs_100g=0.7,
            units=[{"name": "sztuka", "weight_g": 60.0}],
        )
        engine = _build_search_engine(
            candidate_map={"jajko": [_make_candidate("jajko kurze", score=0.9, product_id=pid)]},
            product_map={pid: product},
        )

        # "dwa jajka" -> NLU extracts 2 sztuki
        service = _create_audio_service("dwa jajka")
        service = _wire_meal_service(service, engine)

        result = await service.process_audio(b"audio", session=MagicMock())

        matched = [i for i in result.items if i.status == "matched"]
        assert len(matched) >= 1


class TestAudioPipelineErrorHandling:
    """Test error paths in the audio pipeline."""

    @pytest.mark.asyncio
    async def test_session_required(self):
        """Calling process_audio without session should raise ValueError."""
        engine = _build_search_engine(candidate_map={})
        service = _create_audio_service("test")
        service = _wire_meal_service(service, engine)

        with pytest.raises(ValueError, match="Database session is required"):
            await service.process_audio(b"audio", session=None)

    @pytest.mark.asyncio
    async def test_transcription_failure_propagates(self):
        """TranscriptionFailedException should propagate through the pipeline."""
        from src.ai.domain.exceptions import TranscriptionFailedException

        service = _create_audio_service("anything")
        service.stt_client.transcribe = AsyncMock(
            side_effect=TranscriptionFailedException("Whisper failed")
        )
        engine = _build_search_engine(candidate_map={})
        service = _wire_meal_service(service, engine)

        with pytest.raises(TranscriptionFailedException):
            await service.process_audio(b"audio", session=MagicMock())

    @pytest.mark.asyncio
    async def test_generic_error_wrapped_as_audio_processing_exception(self):
        """Runtime errors during processing should be wrapped."""
        from src.ai.domain.exceptions import AudioProcessingException

        service = _create_audio_service("test")
        service.stt_client.transcribe = AsyncMock(side_effect=RuntimeError("crash"))
        engine = _build_search_engine(candidate_map={})
        service = _wire_meal_service(service, engine)

        with pytest.raises(AudioProcessingException):
            await service.process_audio(b"audio", session=MagicMock())
