import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import unittest.mock
from uuid import uuid4

from src.main import app
from src.users.domain.models import User

@pytest.fixture
def test_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        hashed_password="hashed"
    )

@pytest.fixture
def client():
    # Patch AI services imported in main.py to prevent loading models
    with unittest.mock.patch("src.main.get_audio_service") as mock_audio, \
         unittest.mock.patch("src.main.get_vision_service") as mock_vision:
        
        mock_audio_service = AsyncMock()
        mock_audio_service.warmup = AsyncMock()
        mock_audio.return_value = mock_audio_service
        
        mock_vision.return_value = AsyncMock()
        
        with TestClient(app) as c:
            yield c
        
        app.dependency_overrides = {}
