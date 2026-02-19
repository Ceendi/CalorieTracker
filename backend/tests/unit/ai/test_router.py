"""
Tests for AI API router.

Target: src/ai/api/router.py
Mocks: Override get_audio_service/get_vision_service/get_db_session FastAPI deps
"""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ai.api.router import router, get_audio_service, get_vision_service, current_active_user
from src.users.domain.models import User
from src.ai.application.dto import ProcessedMealDTO, ProcessedFoodItemDTO
from src.ai.domain.exceptions import (
    AudioProcessingException,
    TranscriptionFailedException,
    AudioFormatError,
    AudioTooLongError,
)
from src.core.database import get_db_session


def _make_processed_meal_dto():
    return ProcessedMealDTO(
        meal_type="lunch",
        items=[
            ProcessedFoodItemDTO(
                product_id=uuid.uuid4(),
                name="ryż biały",
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
        ],
        raw_transcription="200g ryżu",
        processing_time_ms=150.0,
    )


@pytest.fixture
def mock_audio_service():
    service = MagicMock()
    service.process_audio = AsyncMock(return_value=_make_processed_meal_dto())
    service.transcribe_only = AsyncMock(return_value="test transcription")
    service.get_system_status = MagicMock(return_value={
        "whisper_available": True,
        "slm_available": False,
        "search_mode": "pgvector",
        "pgvector_service_ready": True,
    })
    return service


@pytest.fixture
def mock_vision_service():
    service = MagicMock()
    service.process_image = AsyncMock(return_value=_make_processed_meal_dto())
    service.get_system_status = MagicMock(return_value={
        "gemini_vision_available": True,
        "pgvector_service_ready": True,
    })
    return service


@pytest.fixture
def client(mock_audio_service, mock_vision_service):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/ai")

    async def mock_db_session():
        yield MagicMock()

    async def mock_user():
        return User(id=uuid.uuid4(), email="test@example.com", is_active=True, is_superuser=False, hashed_password="pwd")

    app.dependency_overrides[get_audio_service] = lambda: mock_audio_service
    app.dependency_overrides[get_vision_service] = lambda: mock_vision_service
    app.dependency_overrides[get_db_session] = mock_db_session
    app.dependency_overrides[current_active_user] = mock_user

    return TestClient(app)


def _make_audio_file(filename="test.mp3", content=b"fake_audio_data"):
    return ("audio", (filename, io.BytesIO(content), "audio/mpeg"))


def _make_image_file(filename="test.jpg", content=b"fake_image_data"):
    return ("image", (filename, io.BytesIO(content), "image/jpeg"))


# ============================================================================
# TestProcessAudioEndpoint
# ============================================================================


class TestProcessAudioEndpoint:
    def test_200_happy_path(self, client):
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type"] == "lunch"
        assert len(data["items"]) == 1

    def test_400_invalid_extension(self, client):
        resp = client.post(
            "/api/v1/ai/process-audio",
            files=[("audio", ("test.txt", io.BytesIO(b"data"), "text/plain"))],
        )
        assert resp.status_code == 400
        assert "Invalid file format" in resp.json()["detail"]

    def test_400_no_filename(self, client):
        resp = client.post(
            "/api/v1/ai/process-audio",
            files=[("audio", ("", io.BytesIO(b"data"), "audio/mpeg"))],
        )
        # Empty string filename → falsy → 400 from route check
        assert resp.status_code in (400, 422)

    def test_400_empty_file(self, client):
        resp = client.post(
            "/api/v1/ai/process-audio",
            files=[_make_audio_file(content=b"")],
        )
        assert resp.status_code == 400
        assert "Empty" in resp.json()["detail"]

    def test_413_oversized(self, client, mock_audio_service):
        huge_content = b"x" * (26 * 1024 * 1024)  # > 25MB
        resp = client.post(
            "/api/v1/ai/process-audio",
            files=[_make_audio_file(content=huge_content)],
        )
        assert resp.status_code == 413

    def test_422_transcription_failed(self, client, mock_audio_service):
        mock_audio_service.process_audio.side_effect = TranscriptionFailedException("STT failed")
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 422

    def test_400_audio_format_error(self, client, mock_audio_service):
        mock_audio_service.process_audio.side_effect = AudioFormatError("Bad format")
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 400

    def test_400_audio_too_long_error(self, client, mock_audio_service):
        mock_audio_service.process_audio.side_effect = AudioTooLongError(120.0, 60.0)
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 400

    def test_500_audio_processing_exception(self, client, mock_audio_service):
        mock_audio_service.process_audio.side_effect = AudioProcessingException("Processing error")
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 500

    def test_500_unexpected(self, client, mock_audio_service):
        mock_audio_service.process_audio.side_effect = RuntimeError("Unexpected")
        resp = client.post("/api/v1/ai/process-audio", files=[_make_audio_file()])
        assert resp.status_code == 500


# ============================================================================
# TestTranscribeEndpoint
# ============================================================================


class TestTranscribeEndpoint:
    def test_happy_path(self, client):
        resp = client.post(
            "/api/v1/ai/transcribe",
            files=[_make_audio_file()],
        )
        assert resp.status_code == 200
        assert resp.json()["transcription"] == "test transcription"

    def test_400_empty_file(self, client):
        resp = client.post(
            "/api/v1/ai/transcribe",
            files=[_make_audio_file(content=b"")],
        )
        assert resp.status_code == 400
        assert "Empty" in resp.json()["detail"]

    def test_422_transcription_failed(self, client, mock_audio_service):
        mock_audio_service.transcribe_only.side_effect = TranscriptionFailedException("fail")
        resp = client.post(
            "/api/v1/ai/transcribe",
            files=[_make_audio_file()],
        )
        assert resp.status_code == 422

    def test_500_unexpected(self, client, mock_audio_service):
        mock_audio_service.transcribe_only.side_effect = RuntimeError("crash")
        resp = client.post(
            "/api/v1/ai/transcribe",
            files=[_make_audio_file()],
        )
        assert resp.status_code == 500


# ============================================================================
# TestProcessImageEndpoint
# ============================================================================


class TestProcessImageEndpoint:
    def test_200_happy_path(self, client):
        resp = client.post(
            "/api/v1/ai/process-image",
            files=[_make_image_file()],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_type"] == "lunch"

    def test_400_invalid_extension(self, client):
        resp = client.post(
            "/api/v1/ai/process-image",
            files=[("image", ("test.bmp", io.BytesIO(b"data"), "image/bmp"))],
        )
        assert resp.status_code == 400

    def test_400_empty(self, client):
        resp = client.post(
            "/api/v1/ai/process-image",
            files=[_make_image_file(content=b"")],
        )
        assert resp.status_code == 400

    def test_413_oversized(self, client):
        huge = b"x" * (11 * 1024 * 1024)
        resp = client.post(
            "/api/v1/ai/process-image",
            files=[_make_image_file(content=huge)],
        )
        assert resp.status_code == 413

    def test_500_unexpected(self, client, mock_vision_service):
        mock_vision_service.process_image.side_effect = RuntimeError("crash")
        resp = client.post(
            "/api/v1/ai/process-image",
            files=[_make_image_file()],
        )
        assert resp.status_code == 500


# ============================================================================
# TestStatusEndpoint
# ============================================================================


class TestStatusEndpoint:
    def test_returns_combined_status(self, client):
        resp = client.get("/api/v1/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "whisper_available" in data
        assert "gemini_vision_available" in data
        assert "search_mode" in data

    def test_status_values(self, client):
        resp = client.get("/api/v1/ai/status")
        data = resp.json()
        assert data["whisper_available"] is True
        assert data["gemini_vision_available"] is True
        assert data["search_mode"] == "pgvector"
