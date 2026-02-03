"""
Integration tests for the AI FastAPI router.

Tests the full HTTP request -> response cycle with real service wiring.
Only external AI services and the database are mocked:
  - STT (Whisper) — returns controlled Polish transcription
  - VisionExtractor (Gemini) — returns controlled extraction results
  - PgVectorSearchService / get_embedding_service — heavy model imports
  - SearchEnginePort — returns controlled search candidates
  - Database session — MagicMock

Real components under test:
  - FastAPI router (request validation, error handling, dependency injection)
  - AudioProcessingService (full orchestration)
  - VisionProcessingService (full orchestration)
  - NaturalLanguageProcessor (normalization, chunking)
  - MealRecognitionService (scoring, matching)
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ai.api.router import router, get_audio_service, get_vision_service
from src.ai.domain.models import (
    SearchCandidate,
    ExtractedFoodItem,
    MealExtraction,
    MealType,
)
from src.ai.domain.exceptions import (
    TranscriptionFailedException,
    AudioProcessingException,
    AudioFormatError,
    AudioTooLongError,
)
from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.core.database import get_db_session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pid() -> str:
    return str(uuid.uuid4())


def _candidate(name, score=0.85, category="UNKNOWN", product_id=None):
    return SearchCandidate(
        product_id=product_id or _pid(),
        name=name, score=score, category=category, passed_guard=True,
    )


def _product(
    name_pl="ryż biały", kcal_100g=130.0, protein_100g=2.7,
    fat_100g=0.3, carbs_100g=28.0, units=None,
):
    return {
        "id": _pid(), "name_pl": name_pl, "name_en": "",
        "kcal_100g": kcal_100g, "protein_100g": protein_100g,
        "fat_100g": fat_100g, "carbs_100g": carbs_100g,
        "category": "CERE", "units": units or [],
    }


def _build_engine(candidate_map, product_map=None):
    engine = MagicMock()
    product_map = product_map or {}

    async def _search(query, top_k=20, alpha=0.3):
        q = query.lower()
        for key, candidates in candidate_map.items():
            if key in q:
                return candidates
        return []

    engine.search = AsyncMock(side_effect=_search)
    engine.get_product_by_id = MagicMock(
        side_effect=lambda pid: product_map.get(pid, _product())
    )
    engine.index_products = MagicMock()
    return engine


def _make_extraction(items=None, meal_type=MealType.LUNCH):
    return MealExtraction(
        meal_type=meal_type,
        raw_transcription="[Analiza Obrazu]",
        items=items or [],
        overall_confidence=0.9,
    )


def _audio_file(filename="test.mp3", content=b"fake_audio"):
    return ("audio", (filename, io.BytesIO(content), "audio/mpeg"))


def _image_file(filename="test.jpg", content=b"fake_image"):
    return ("image", (filename, io.BytesIO(content), "image/jpeg"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def audio_search_engine():
    """Search engine for audio tests with common Polish foods."""
    pid_r = _pid()
    pid_k = _pid()
    return _build_engine(
        candidate_map={
            "ryż": [_candidate("ryż biały", score=0.85, product_id=pid_r)],
            "pierś": [_candidate("pierś z kurczaka", score=0.80, product_id=pid_k)],
            "kurczak": [_candidate("pierś z kurczaka", score=0.80, product_id=pid_k)],
        },
        product_map={
            pid_r: _product(name_pl="ryż biały", kcal_100g=130.0),
            pid_k: _product(name_pl="pierś z kurczaka", kcal_100g=110.0, protein_100g=23.0),
        },
    )


@pytest.fixture
def vision_search_engine():
    """Search engine for vision tests."""
    pid = _pid()
    return _build_engine(
        candidate_map={
            "ryż": [_candidate("ryż biały", score=0.85, product_id=pid)],
        },
        product_map={pid: _product(name_pl="ryż biały", kcal_100g=130.0)},
    )


def _create_real_audio_service(transcription: str, search_engine):
    """Create a real AudioProcessingService with mocked STT and controlled search."""
    mock_stt = MagicMock()
    mock_stt.transcribe = AsyncMock(return_value=transcription)
    mock_stt.is_available = MagicMock(return_value=True)
    mock_stt.load_model = AsyncMock()

    mock_slm = MagicMock()
    mock_slm.is_available = MagicMock(return_value=False)

    with patch("src.ai.infrastructure.search.PgVectorSearchService") as mock_pvs, \
         patch("src.ai.infrastructure.embedding.get_embedding_service") as mock_ges:
        mock_ges.return_value = MagicMock()
        mock_pvs.return_value = MagicMock()

        from src.ai.application.audio_service import AudioProcessingService
        service = AudioProcessingService(
            stt_client=mock_stt,
            nlu_processor=NaturalLanguageProcessor(),
            slm_extractor=mock_slm,
        )

    from src.ai.application.meal_service import MealRecognitionService

    def _get_meal_service(session):
        return MealRecognitionService(
            vector_engine=search_engine,
            nlu_processor=service.nlu_processor,
            slm_extractor=None,
        )

    service._get_meal_service = _get_meal_service
    return service


def _create_real_vision_service(extraction_result, search_engine):
    """Create a real VisionProcessingService with mocked extractor and controlled search."""
    with patch("src.ai.infrastructure.search.PgVectorSearchService") as mock_pvs, \
         patch("src.ai.infrastructure.embedding.get_embedding_service") as mock_ges, \
         patch("src.ai.application.vision_service.VisionExtractor") as mock_ve:
        mock_ges.return_value = MagicMock()
        mock_pvs.return_value = MagicMock()

        mock_ve_instance = MagicMock()
        mock_ve_instance.client = MagicMock()
        mock_ve_instance.extract_from_image = AsyncMock(return_value=extraction_result)
        mock_ve.return_value = mock_ve_instance

        from src.ai.application.vision_service import VisionProcessingService
        service = VisionProcessingService()

    from src.ai.application.meal_service import MealRecognitionService

    def _get_meal_service(session):
        return MealRecognitionService(
            vector_engine=search_engine,
            nlu_processor=service.nlu_processor,
            slm_extractor=None,
        )

    service._get_meal_service = _get_meal_service
    return service


@pytest.fixture
def audio_client(audio_search_engine):
    """TestClient wired with real audio service pipeline."""
    audio_service = _create_real_audio_service("200g ryżu", audio_search_engine)

    vision_service = MagicMock()
    vision_service.get_system_status = MagicMock(return_value={
        "gemini_vision_available": True, "pgvector_service_ready": True,
    })

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/ai")

    async def mock_db_session():
        yield MagicMock()

    app.dependency_overrides[get_audio_service] = lambda: audio_service
    app.dependency_overrides[get_vision_service] = lambda: vision_service
    app.dependency_overrides[get_db_session] = mock_db_session

    return TestClient(app)


@pytest.fixture
def vision_client(vision_search_engine):
    """TestClient wired with real vision service pipeline."""
    extraction = (
        _make_extraction(items=[
            ExtractedFoodItem(name="ryż biały", quantity_value=200.0, quantity_unit="g"),
        ]),
        0.9,
    )
    vision_service = _create_real_vision_service(extraction, vision_search_engine)

    audio_service = MagicMock()
    audio_service.get_system_status = MagicMock(return_value={
        "whisper_available": True, "slm_available": False,
        "search_mode": "pgvector", "pgvector_service_ready": True,
    })

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/ai")

    async def mock_db_session():
        yield MagicMock()

    app.dependency_overrides[get_audio_service] = lambda: audio_service
    app.dependency_overrides[get_vision_service] = lambda: vision_service
    app.dependency_overrides[get_db_session] = mock_db_session

    return TestClient(app)


# ===========================================================================
# Audio Endpoint Integration Tests
# ===========================================================================


class TestProcessAudioEndpointIntegration:
    """Test /process-audio with real service pipeline wiring."""

    def test_200_returns_matched_items(self, audio_client):
        """Full pipeline: audio upload -> STT -> NLU -> search -> matched DTO."""
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[_audio_file()],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type"] in ("snack", "breakfast", "lunch", "dinner")
        assert len(data["items"]) >= 1
        assert data["raw_transcription"] == "200g ryżu"
        assert data["processing_time_ms"] > 0

        # First item should be matched rice
        first_item = data["items"][0]
        assert first_item["status"] == "matched"
        assert first_item["quantity_grams"] == 200.0

    def test_200_items_have_correct_dto_fields(self, audio_client):
        """All DTO fields should be present in the response."""
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[_audio_file()],
        )
        data = resp.json()
        item = data["items"][0]

        required_fields = [
            "product_id", "name", "quantity_grams", "kcal", "protein",
            "fat", "carbs", "confidence", "unit_matched",
            "quantity_unit_value", "status", "units",
        ]
        for field in required_fields:
            assert field in item, f"Missing field: {field}"

    def test_400_invalid_format(self, audio_client):
        """Invalid file extension should return 400."""
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[("audio", ("test.txt", io.BytesIO(b"data"), "text/plain"))],
        )
        assert resp.status_code == 400
        assert "Invalid file format" in resp.json()["detail"]

    def test_400_empty_file(self, audio_client):
        """Empty audio file should return 400."""
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[_audio_file(content=b"")],
        )
        assert resp.status_code == 400
        assert "Empty" in resp.json()["detail"]

    def test_413_oversized_file(self, audio_client):
        """File exceeding 25MB should return 413."""
        huge = b"x" * (26 * 1024 * 1024)
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[_audio_file(content=huge)],
        )
        assert resp.status_code == 413

    def test_multiple_audio_formats_accepted(self, audio_client):
        """Various audio formats should be accepted."""
        for ext, mime in [
            (".wav", "audio/wav"),
            (".mp3", "audio/mpeg"),
            (".m4a", "audio/mp4"),
            (".ogg", "audio/ogg"),
            (".flac", "audio/flac"),
            (".webm", "audio/webm"),
        ]:
            resp = audio_client.post(
                "/api/v1/ai/process-audio",
                files=[("audio", (f"test{ext}", io.BytesIO(b"data"), mime))],
            )
            assert resp.status_code == 200, f"Failed for format {ext}"


class TestProcessAudioErrorChainIntegration:
    """Test error handling chain with real services."""

    def test_transcription_failure_returns_422(self, audio_search_engine):
        """TranscriptionFailedException should surface as 422."""
        audio_service = _create_real_audio_service("test", audio_search_engine)
        audio_service.stt_client.transcribe = AsyncMock(
            side_effect=TranscriptionFailedException("STT crash")
        )

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/ai")

        async def mock_db():
            yield MagicMock()

        mock_vision = MagicMock()
        mock_vision.get_system_status = MagicMock(return_value={})
        app.dependency_overrides[get_audio_service] = lambda: audio_service
        app.dependency_overrides[get_vision_service] = lambda: mock_vision
        app.dependency_overrides[get_db_session] = mock_db

        client = TestClient(app)
        resp = client.post("/api/v1/ai/process-audio", files=[_audio_file()])
        assert resp.status_code == 422

    def test_http_exception_not_wrapped(self, audio_client):
        """HTTPException raised by validation should not be wrapped."""
        # No filename -> 400 from route check
        resp = audio_client.post(
            "/api/v1/ai/process-audio",
            files=[("audio", ("", io.BytesIO(b"data"), "audio/mpeg"))],
        )
        assert resp.status_code in (400, 422)


# ===========================================================================
# Vision Endpoint Integration Tests
# ===========================================================================


class TestProcessImageEndpointIntegration:
    """Test /process-image with real service pipeline wiring."""

    def test_200_returns_matched_items(self, vision_client):
        """Full pipeline: image upload -> Gemini -> search -> matched DTO."""
        resp = vision_client.post(
            "/api/v1/ai/process-image",
            files=[_image_file()],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type"] in ("snack", "breakfast", "lunch", "dinner")
        assert len(data["items"]) >= 1
        assert data["processing_time_ms"] > 0

    def test_200_items_have_correct_fields(self, vision_client):
        """All expected DTO fields should be present."""
        resp = vision_client.post(
            "/api/v1/ai/process-image",
            files=[_image_file()],
        )
        data = resp.json()
        item = data["items"][0]

        for field in ["product_id", "name", "quantity_grams", "kcal", "status"]:
            assert field in item

    def test_400_invalid_image_format(self, vision_client):
        """Invalid image extension should return 400."""
        resp = vision_client.post(
            "/api/v1/ai/process-image",
            files=[("image", ("test.bmp", io.BytesIO(b"data"), "image/bmp"))],
        )
        assert resp.status_code == 400

    def test_400_empty_image(self, vision_client):
        """Empty image file should return 400."""
        resp = vision_client.post(
            "/api/v1/ai/process-image",
            files=[_image_file(content=b"")],
        )
        assert resp.status_code == 400

    def test_413_oversized_image(self, vision_client):
        """Image exceeding 10MB should return 413."""
        huge = b"x" * (11 * 1024 * 1024)
        resp = vision_client.post(
            "/api/v1/ai/process-image",
            files=[_image_file(content=huge)],
        )
        assert resp.status_code == 413

    def test_multiple_image_formats_accepted(self, vision_client):
        """Various image formats should be accepted."""
        for ext, mime in [
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
            (".png", "image/png"),
            (".webp", "image/webp"),
            (".heic", "image/heic"),
        ]:
            resp = vision_client.post(
                "/api/v1/ai/process-image",
                files=[("image", (f"test{ext}", io.BytesIO(b"data"), mime))],
            )
            assert resp.status_code == 200, f"Failed for format {ext}"


# ===========================================================================
# Status Endpoint Integration Tests
# ===========================================================================


class TestStatusEndpointIntegration:
    """Test /status endpoint with real service wiring."""

    def test_returns_combined_status(self, audio_client):
        """Status endpoint should combine audio and vision service status."""
        resp = audio_client.get("/api/v1/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "whisper_available" in data
        assert "search_mode" in data

    def test_status_values(self, audio_client):
        """Status values should reflect mocked service state."""
        resp = audio_client.get("/api/v1/ai/status")
        data = resp.json()
        assert data["whisper_available"] is True
        assert data["search_mode"] == "pgvector"


# ===========================================================================
# Transcribe Endpoint Integration Tests
# ===========================================================================


class TestTranscribeEndpointIntegration:
    """Test /transcribe endpoint with real audio service."""

    def test_returns_transcription(self, audio_client):
        """Transcribe endpoint should return the raw transcription."""
        resp = audio_client.post(
            "/api/v1/ai/transcribe",
            files=[_audio_file()],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transcription"] == "200g ryżu"
        assert data["language"] == "pl"

    def test_400_empty_audio(self, audio_client):
        """Empty audio should return 400."""
        resp = audio_client.post(
            "/api/v1/ai/transcribe",
            files=[_audio_file(content=b"")],
        )
        assert resp.status_code == 400
