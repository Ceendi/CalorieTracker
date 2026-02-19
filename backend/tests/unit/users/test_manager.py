import pytest
import base64
from unittest.mock import AsyncMock, patch
from fastapi_users.exceptions import InvalidVerifyToken, UserAlreadyVerified

from src.users.application.manager import UserManager
from src.users.domain.models import User

@pytest.fixture
def mock_user_db():
    return AsyncMock()

@pytest.fixture
def manager(mock_user_db):
    return UserManager(mock_user_db)

@pytest.fixture
def user():
    return User(
        id="00000000-0000-0000-0000-000000000000",
        email="test@example.com",
        is_verified=False,
        verification_code="123456"
    )

@pytest.mark.asyncio
async def test_validate_verify_token_success(manager, user):
    # Arrange
    token = base64.b64encode(b"test@example.com:123456").decode('utf-8')
    manager.get_by_email = AsyncMock(return_value=user)

    # Act
    result = await manager.validate_verify_token(token)

    # Assert
    assert result == user
    manager.get_by_email.assert_called_once_with("test@example.com")

@pytest.mark.asyncio
async def test_validate_verify_token_invalid_format(manager):
    # Act & Assert
    with pytest.raises(InvalidVerifyToken):
        await manager.validate_verify_token("invalid_base64")

@pytest.mark.asyncio
async def test_validate_verify_token_user_not_found(manager):
    # Arrange
    token = base64.b64encode(b"missing@example.com:123456").decode('utf-8')
    manager.get_by_email = AsyncMock(return_value=None)

    # Act & Assert
    with pytest.raises(InvalidVerifyToken):
        await manager.validate_verify_token(token)

@pytest.mark.asyncio
async def test_validate_verify_token_wrong_code(manager, user):
    # Arrange
    token = base64.b64encode(b"test@example.com:654321").decode('utf-8')
    manager.get_by_email = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(InvalidVerifyToken):
        await manager.validate_verify_token(token)

@pytest.mark.asyncio
async def test_verify_success(manager, user, mock_user_db):
    # Arrange
    token = "some_token"
    manager.validate_verify_token = AsyncMock(return_value=user)
    manager.on_after_verify = AsyncMock()

    # Act
    result = await manager.verify(token)

    # Assert
    assert result == user
    mock_user_db.update.assert_called_once_with(user, {"is_verified": True})
    manager.on_after_verify.assert_called_once_with(user, None)

@pytest.mark.asyncio
async def test_verify_already_verified(manager, user):
    # Arrange
    user.is_verified = True
    manager.validate_verify_token = AsyncMock(return_value=user)

    # Act & Assert
    with pytest.raises(UserAlreadyVerified):
        await manager.verify("token")

@pytest.mark.asyncio
async def test_request_verify_success(manager, user, mock_user_db):
    # Arrange
    manager.on_after_request_verify = AsyncMock()

    # Act
    with patch('secrets.randbelow', return_value=899999):
        await manager.request_verify(user)

    # Assert
    mock_user_db.update.assert_called_once_with(user, {"verification_code": "999999"})
    manager.on_after_request_verify.assert_called_once_with(user, "999999", None)

@pytest.mark.asyncio
async def test_on_after_register_needs_verify(manager, user):
    # Arrange
    manager.request_verify = AsyncMock()

    # Act
    await manager.on_after_register(user)

    # Assert
    manager.request_verify.assert_called_once_with(user, None)

@pytest.mark.asyncio
async def test_on_after_register_already_verified(manager, user):
    # Arrange
    user.is_verified = True
    manager.request_verify = AsyncMock()

    # Act
    await manager.on_after_register(user)

    # Assert
    manager.request_verify.assert_not_called()

@pytest.mark.asyncio
async def test_on_after_forgot_password(manager, user):
    # Act
    await manager.on_after_forgot_password(user, "reset_token")
    # Assert (mostly coverage for logger simulation)

@pytest.mark.asyncio
async def test_verify_generic_exception(manager):
    # Arrange
    manager.validate_verify_token = AsyncMock(side_effect=ValueError("Generic error"))
    # Act & Assert
    with pytest.raises(ValueError):
        await manager.verify("token")
