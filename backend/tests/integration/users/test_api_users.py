import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from uuid import uuid4
from src.main import app
from src.users.application.manager import get_user_manager
from src.users.api.routes import current_active_user

@pytest.fixture
def mock_user_manager():
    return AsyncMock()

@pytest.mark.asyncio
async def test_change_password_success(client, mock_user_manager):
    # Arrange
    mock_user = MagicMock()
    mock_user.hashed_password = "hashed_old_password"
    
    mock_user_manager.password_helper = MagicMock()
    mock_user_manager.password_helper.verify_and_update.return_value = (True, "hashed_old_password")
    mock_user_manager.password_helper.hash.return_value = "hashed_new_password"
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    app.dependency_overrides[current_active_user] = lambda: mock_user
    
    try:
        response = client.post(
            "/users/change-password",
            json={"old_password": "OldPassword123", "new_password": "NewPassword123"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "Password updated successfully"
        mock_user_manager.user_db.update.assert_called_once()
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_change_password_invalid_old(client, mock_user_manager):
    # Arrange
    mock_user = MagicMock()
    mock_user.hashed_password = "hashed_old_password"
    mock_user_manager.password_helper = MagicMock()
    mock_user_manager.password_helper.verify_and_update.return_value = (False, None)
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    app.dependency_overrides[current_active_user] = lambda: mock_user
    
    try:
        response = client.post(
            "/users/change-password",
            json={"old_password": "WrongPassword123", "new_password": "NewPassword123"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid old password"
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_change_password_not_set(client, mock_user_manager):
    # Arrange
    mock_user = MagicMock()
    mock_user.hashed_password = None
    
    app.dependency_overrides[get_user_manager] = lambda: mock_user_manager
    app.dependency_overrides[current_active_user] = lambda: mock_user
    
    try:
        response = client.post(
            "/users/change-password",
            json={"old_password": "OldPassword123", "new_password": "NewPassword123"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "User has no password set"
    finally:
        app.dependency_overrides = {}
