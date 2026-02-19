import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from fastapi import HTTPException

from src.users.application.services import AuthService
from src.users.domain.models import User
from src.users.infrastructure.models import RefreshToken

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_repo):
    return AuthService(mock_repo)

@pytest.fixture
def user():
    return User(
        id="00000000-0000-0000-0000-000000000000",
        email="test@example.com",
        is_active=True
    )

@pytest.mark.asyncio
async def test_create_tokens(service, mock_repo, user):
    # Arrange
    mock_strategy = AsyncMock()
    mock_strategy.write_token.return_value = "access_token"

    # Act
    result = await service.create_tokens(user, mock_strategy)

    # Assert
    assert result["access_token"] == "access_token"
    assert "refresh_token" in result
    mock_repo.add_token.assert_called_once()
    mock_repo.commit.assert_called_once()

@pytest.mark.asyncio
async def test_refresh_session_success(service, mock_repo, user):
    # Arrange
    refresh_token = "valid_token"
    token_hash = RefreshToken.hash_token(refresh_token)
    db_token = RefreshToken(user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    
    mock_repo.get_token.return_value = db_token
    mock_user_manager = AsyncMock()
    mock_user_manager.get.return_value = user
    mock_strategy = AsyncMock()
    mock_strategy.write_token.return_value = "new_access_token"

    # Act
    result = await service.refresh_session(refresh_token, mock_strategy, mock_user_manager)

    # Assert
    assert result["access_token"] == "new_access_token"
    mock_repo.delete_token.assert_called_once_with(token_hash)

@pytest.mark.asyncio
async def test_refresh_session_invalid_token(service, mock_repo):
    # Arrange
    mock_repo.get_token.return_value = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await service.refresh_session("invalid", AsyncMock(), AsyncMock())
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_refresh_session_expired(service, mock_repo):
    # Arrange
    refresh_token = "expired_token"
    token_hash = RefreshToken.hash_token(refresh_token)
    db_token = RefreshToken(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    mock_repo.get_token.return_value = db_token
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await service.refresh_session(refresh_token, AsyncMock(), AsyncMock())
    assert exc.value.status_code == 401
    mock_repo.delete_token.assert_called_once_with(token_hash)
    mock_repo.commit.assert_called()

@pytest.mark.asyncio
async def test_logout(service, mock_repo):
    # Arrange
    refresh_token = "logout_token"
    token_hash = RefreshToken.hash_token(refresh_token)

    # Act
    await service.logout(refresh_token)

    # Assert
    mock_repo.delete_token.assert_called_once_with(token_hash)
    mock_repo.commit.assert_called_once()

@pytest.mark.asyncio
async def test_refresh_session_user_inactive(service, mock_repo, user):
    # Arrange
    user.is_active = False
    mock_repo.get_token.return_value = RefreshToken(user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    mock_user_manager = AsyncMock()
    mock_user_manager.get.return_value = user
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await service.refresh_session("token", AsyncMock(), mock_user_manager)
    assert exc.value.status_code == 401
    assert exc.value.detail == "User inactive"
