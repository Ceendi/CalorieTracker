"""
Integration tests for the vision processing pipeline.

Tests the full vision pipeline:
  VisionExtractor (mocked) -> MealRecognitionService (real scoring) -> DTO output

Only external services are mocked:
  - VisionExtractor (Gemini API) — returns controlled ExtractedFoodItem lists
  - PgVectorSearchService / get_embedding_service — heavy model imports
  - SearchEnginePort — returns controlled search candidates (simulates DB)

Real components under test:
  - NaturalLanguageProcessor (text normalization, keyword consistency guard)
  - MealRecognitionService (vision scoring, DB-vs-fallback logic, grams calculation)
  - VisionProcessingService (orchestration, DTO building)
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.application.dto import ProcessedMealDTO
from src.ai.domain.models import (
    SearchCandidate,
    ExtractedFoodItem,
    MealExtraction,
    MealType,
)
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor


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


def _make_extraction(
    items: list = None,
    meal_type: MealType = MealType.LUNCH,
) -> MealExtraction:
    return MealExtraction(
        meal_type=meal_type,
        raw_transcription="[Analiza Obrazu]",
        items=items or [],
        overall_confidence=0.9,
    )


def _build_search_engine(candidate_map: dict, product_map: dict = None):
    """Build a mock SearchEnginePort with controlled responses per query."""
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


def _create_vision_service():
    """
    Create a VisionProcessingService with real NLU, mocked VisionExtractor,
    and mocked heavy imports. Returns (service, mock_vision_extractor).
    """
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


def _wire_meal_service(service, search_engine):
    """
    Replace _get_meal_service on the vision service to use a
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


class TestVisionPipelineDBMatch:
    """Test vision pipeline when DB search finds a good match (score > 0.5)."""

    @pytest.mark.asyncio
    async def test_single_item_db_match(self):
        """A single extracted item with a strong DB match should have status='matched'."""
        pid = _make_product_id()
        product = _make_product_dict(
            name_pl="ryż biały", kcal_100g=130.0,
            protein_100g=2.7, fat_100g=0.3, carbs_100g=28.0,
        )
        engine = _build_search_engine(
            candidate_map={"ryż": [_make_candidate("ryż biały", score=0.80, product_id=pid)]},
            product_map={pid: product},
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="ryż biały", quantity_value=200.0, quantity_unit="g",
                    kcal=260.0, protein=5.4, fat=0.6, carbs=56.0,
                )
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert isinstance(result, ProcessedMealDTO)
        assert len(result.items) == 1
        assert result.items[0].status == "matched"
        # DB macros should be used (200g -> 2x 130kcal = 260)
        assert result.items[0].kcal == pytest.approx(260.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_multiple_items_all_matched(self):
        """Multiple vision items should each get matched against DB."""
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
                    protein_100g=23.0, fat_100g=1.3, carbs_100g=0.0,
                ),
            },
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(name="ryż biały", quantity_value=200.0, quantity_unit="g"),
                ExtractedFoodItem(name="pierś z kurczaka", quantity_value=150.0, quantity_unit="g"),
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert len(result.items) == 2
        assert all(item.status == "matched" for item in result.items)

    @pytest.mark.asyncio
    async def test_db_macros_override_gemini_macros(self):
        """When DB match is found, DB nutrition values should be used over Gemini estimates."""
        pid = _make_product_id()
        db_product = _make_product_dict(
            name_pl="jajko kurze", kcal_100g=155.0,
            protein_100g=12.6, fat_100g=11.5, carbs_100g=0.7,
        )
        engine = _build_search_engine(
            candidate_map={"jajko": [_make_candidate("jajko kurze", score=0.85, product_id=pid)]},
            product_map={pid: db_product},
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="jajko", quantity_value=100.0, quantity_unit="g",
                    kcal=75.0, protein=6.0, fat=5.0, carbs=0.3,  # Gemini estimate
                )
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        # DB has 155kcal/100g, Gemini estimated 75kcal — DB should win
        assert item.kcal == pytest.approx(155.0, abs=1.0)
        assert item.status == "matched"


class TestVisionPipelineFallback:
    """Test vision pipeline when DB search fails and Gemini fallback is used."""

    @pytest.mark.asyncio
    async def test_low_score_uses_gemini_macros(self):
        """When DB match score < 0.5, Gemini macros should be used (needs_confirmation)."""
        engine = _build_search_engine(
            candidate_map={
                "sushi": [_make_candidate("ryba surowa", score=0.15)],
            },
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="sushi nigiri", quantity_value=150.0, quantity_unit="g",
                    kcal=180.0, protein=12.0, fat=3.0, carbs=28.0, confidence=0.85,
                )
            ]),
            0.85,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        assert item.status == "needs_confirmation"
        # Gemini macros should be used
        assert item.kcal == pytest.approx(180.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_no_search_results_uses_gemini_fallback(self):
        """When no search candidates at all, should fallback to Gemini macros."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="proteinowy koktajl", quantity_value=300.0, quantity_unit="ml",
                    kcal=250.0, protein=30.0, fat=5.0, carbs=15.0,
                )
            ]),
            0.8,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        assert item.status == "needs_confirmation"
        assert item.kcal == pytest.approx(250.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_guard_fail_causes_fallback(self):
        """When keyword consistency guard fails, score should drop below 0.5 threshold."""
        # "kurczak" in query, but "indyk" in candidate -> guard fail
        pid = _make_product_id()
        engine = _build_search_engine(
            candidate_map={
                "kurczak": [_make_candidate("indyk filet", score=0.7, product_id=pid)],
            },
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="kurczak grillowany", quantity_value=150.0, quantity_unit="g",
                    kcal=165.0, protein=31.0, fat=3.6, carbs=0.0,
                )
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        # Guard fail: 0.7 * 0.4 = 0.28, below 0.5 threshold -> fallback
        assert item.status == "needs_confirmation"
        assert item.kcal == pytest.approx(165.0, abs=1.0)


class TestVisionPipelineMealType:
    """Test meal type detection from vision extraction."""

    @pytest.mark.asyncio
    async def test_breakfast_meal_type(self):
        """Vision extraction with breakfast meal type should propagate to DTO."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[], meal_type=MealType.BREAKFAST),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert result.meal_type == "breakfast"

    @pytest.mark.asyncio
    async def test_dinner_meal_type(self):
        """Vision extraction with dinner meal type should propagate."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[], meal_type=MealType.DINNER),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert result.meal_type == "dinner"

    @pytest.mark.asyncio
    async def test_snack_meal_type(self):
        """Vision extraction with snack meal type should propagate."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[], meal_type=MealType.SNACK),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert result.meal_type == "snack"


class TestVisionPipelineEmptyExtraction:
    """Test behavior when Gemini returns no items."""

    @pytest.mark.asyncio
    async def test_empty_items_returns_empty_dto(self):
        """Empty extraction should produce an empty DTO."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[]),
            0.0,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert len(result.items) == 0
        assert result.raw_transcription == "[Analiza Obrazu]"

    @pytest.mark.asyncio
    async def test_processing_time_positive(self):
        """Processing time should be recorded even for empty results."""
        engine = _build_search_engine(candidate_map={})

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[]),
            0.0,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        assert result.processing_time_ms > 0


class TestVisionPipelineUnitHandling:
    """Test that various unit types from vision are correctly handled."""

    @pytest.mark.asyncio
    async def test_sztuka_unit_uses_product_units(self):
        """When vision reports 'sztuka', should use product unit weight from DB."""
        pid = _make_product_id()
        product = _make_product_dict(
            name_pl="jajko kurze", kcal_100g=155.0,
            protein_100g=12.6, fat_100g=11.5, carbs_100g=0.7,
            units=[{"name": "sztuka", "weight_g": 60.0}],
        )
        engine = _build_search_engine(
            candidate_map={"jajko": [_make_candidate("jajko kurze", score=0.85, product_id=pid)]},
            product_map={pid: product},
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="jajko", quantity_value=3.0, quantity_unit="sztuka",
                    kcal=75.0, protein=6.0, fat=5.0, carbs=0.3,
                )
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        assert item.status == "matched"
        # 3 sztuki * 60g = 180g -> 1.8 * 155 = 279 kcal
        assert item.quantity_grams == pytest.approx(180.0, abs=1.0)
        assert item.kcal == pytest.approx(279.0, abs=1.0)

    @pytest.mark.asyncio
    async def test_gram_unit_passed_directly(self):
        """When vision reports 'g' unit, grams should be used directly."""
        pid = _make_product_id()
        product = _make_product_dict(
            name_pl="pierś z kurczaka", kcal_100g=110.0,
            protein_100g=23.0, fat_100g=1.3, carbs_100g=0.0,
        )
        engine = _build_search_engine(
            candidate_map={
                "pierś": [_make_candidate("pierś z kurczaka", score=0.80, product_id=pid)],
                "kurczak": [_make_candidate("pierś z kurczaka", score=0.80, product_id=pid)],
            },
            product_map={pid: product},
        )

        service, mock_extractor = _create_vision_service()
        mock_extractor.extract_from_image.return_value = (
            _make_extraction(items=[
                ExtractedFoodItem(
                    name="pierś z kurczaka", quantity_value=200.0, quantity_unit="g",
                )
            ]),
            0.9,
        )
        service = _wire_meal_service(service, engine)

        result = await service.process_image(b"image", session=MagicMock())

        item = result.items[0]
        assert item.quantity_grams == pytest.approx(200.0, abs=1.0)
        assert item.kcal == pytest.approx(220.0, abs=1.0)


class TestVisionPipelineSessionValidation:
    """Test session validation in vision pipeline."""

    @pytest.mark.asyncio
    async def test_none_session_raises_value_error(self):
        """Passing None session should raise ValueError."""
        service, _ = _create_vision_service()
        with pytest.raises(ValueError, match="Database session is required"):
            await service.process_image(b"image", session=None)
