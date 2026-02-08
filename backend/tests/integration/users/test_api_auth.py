import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from httpx import Response
from uuid import uuid4
from src.main import app
from src.users.application.manager import get_user_manager
from src.users.api.dependencies import get_auth_service

@pytest.fixture
def mock_user_manager():
    return AsyncMock()

@pytest.fixture
def mock_auth_service():
    return AsyncMock()

@pytest.mark.asyncio
async def test_login_success(client, mock_user_manager, mock_auth_service):
    # Arrange
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_user.id = uuid4()
    
    mock_user_manager.authenticate.return_value = mock_user
    mock_auth_service.create_tokens.return_value = {"access_token": "token", "refresh_token": "refresh"}
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    try:
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "password"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == "token"
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_login_bad_credentials(client, mock_user_manager):
    # Arrange
    mock_user_manager.authenticate.return_value = None
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    
    try:
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "wrong"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_google_login_success(client, mock_user_manager, mock_auth_service):
    # Arrange
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_user_manager.get_by_email.return_value = mock_user
    mock_auth_service.create_tokens.return_value = {"access_token": "google_token"}

    google_response = Response(
        200, 
        json={"email": "test@google.com", "aud": "dummy_client_id"}
    )
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    with patch("httpx.AsyncClient.get", return_value=google_response), \
         patch("src.users.api.auth_router.settings.GOOGLE_CLIENT_ID", "dummy_client_id"):
        
        try:
            response = client.post(
                "/auth/google",
                json={"token": "valid_google_token"}
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["access_token"] == "google_token"
        finally:
            app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_refresh_token_success(client, mock_auth_service):
    # Arrange
    mock_auth_service.refresh_session.return_value = {"access_token": "new_token"}
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    try:
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["access_token"] == "new_token"
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_logout_success(client, mock_auth_service):
    # Arrange
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    try:
        response = client.post(
            "/auth/logout",
            json={"refresh_token": "some_token"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Logged out successfully"
        mock_auth_service.logout.assert_called_once_with("some_token")
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_google_login_invalid_token(client):
    google_response = Response(400, json={"error": "invalid_token"})
    with patch("httpx.AsyncClient.get", return_value=google_response):
        response = client.post("/auth/google", json={"token": "bad"})
    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_GOOGLE_TOKEN"

@pytest.mark.asyncio
async def test_google_login_bad_audience(client):
    google_response = Response(200, json={"email": "test@google.com", "aud": "wrong_aud"})
    with patch("httpx.AsyncClient.get", return_value=google_response), \
         patch("src.users.api.auth_router.settings.GOOGLE_CLIENT_ID", "expected_aud"):
        response = client.post("/auth/google", json={"token": "token"})
    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_GOOGLE_TOKEN_AUDIENCE"

@pytest.mark.asyncio
async def test_google_login_no_email(client):
    google_response = Response(200, json={"aud": "dummy"})
    with patch("httpx.AsyncClient.get", return_value=google_response), \
         patch("src.users.api.auth_router.settings.GOOGLE_CLIENT_ID", "dummy"):
        response = client.post("/auth/google", json={"token": "token"})
    assert response.status_code == 400
    assert response.json()["detail"] == "GOOGLE_ACCOUNT_NO_EMAIL"

@pytest.mark.asyncio
async def test_google_login_registration_failure(client, mock_user_manager):
    google_response = Response(200, json={"email": "test@google.com", "aud": "dummy"})
    mock_user_manager.get_by_email.return_value = None
    mock_user_manager.create.side_effect = Exception("DB Error")
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    with patch("httpx.AsyncClient.get", return_value=google_response), \
         patch("src.users.api.auth_router.settings.GOOGLE_CLIENT_ID", "dummy"):
        response = client.post("/auth/google", json={"token": "token"})
    app.dependency_overrides = {}
    assert response.status_code == 400
    assert response.json()["detail"] == "REGISTER_FAILED"

@pytest.mark.asyncio
async def test_login_inactive_user(client, mock_user_manager):
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_user_manager.authenticate.return_value = mock_user
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    response = client.post("/auth/login", data={"username": "test", "password": "pwd"})
    app.dependency_overrides = {}
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"

@pytest.mark.asyncio
async def test_google_login_inactive_user(client, mock_user_manager):
    google_response = Response(200, json={"email": "test@google.com", "aud": "dummy"})
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_user_manager.get_by_email.return_value = mock_user
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    with patch("httpx.AsyncClient.get", return_value=google_response), \
         patch("src.users.api.auth_router.settings.GOOGLE_CLIENT_ID", "dummy"):
        response = client.post("/auth/google", json={"token": "token"})
    app.dependency_overrides = {}
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"
