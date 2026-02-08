import pytest
import io
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.users.api.routes import current_active_user
from src.users.domain.models import User

@pytest.fixture
def user_a():
    return User(id=uuid4(), email="user_a@example.com", is_active=True, is_superuser=False, hashed_password="pwd")

@pytest.fixture
def client_anonymous():
    with patch("src.main.get_audio_service"), patch("src.main.get_vision_service"):
        with TestClient(app) as c:
            yield c

def test_process_audio_requires_auth(client_anonymous):
    # Act
    files = {"audio": ("test.mp3", io.BytesIO(b"fake audio data"), "audio/mpeg")}
    response = client_anonymous.post("/api/v1/ai/process-audio", files=files)
    # Assert
    assert response.status_code == 401

def test_process_image_requires_auth(client_anonymous):
    # Act
    files = {"image": ("test.jpg", io.BytesIO(b"fake image data"), "image/jpeg")}
    response = client_anonymous.post("/api/v1/ai/process-image", files=files)
    # Assert
    assert response.status_code == 401

def test_ai_status_requires_auth(client_anonymous):
    # Act
    response = client_anonymous.get("/api/v1/ai/status")
    # Assert
    assert response.status_code == 401
