import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.users.infrastructure.repositories import RefreshTokenRepository
from src.users.infrastructure.models import RefreshToken

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session

@pytest.fixture
def repo(mock_session):
    return RefreshTokenRepository(mock_session)

@pytest.mark.asyncio
async def test_add_token_no_overflow(repo, mock_session):
    # Arrange
    user_id = uuid4()
    token_hash = "some_hash"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    mock_result = MagicMock()
    mock_result.scalar.return_value = 0
    mock_session.execute.return_value = mock_result

    # Act
    await repo.add_token(user_id, token_hash, expires_at)

    # Assert
    mock_session.add.assert_called_once()
    added_token = mock_session.add.call_args[0][0]
    assert isinstance(added_token, RefreshToken)
    assert added_token.user_id == user_id
    assert added_token.token_hash == token_hash
    assert added_token.expires_at == expires_at
    mock_session.flush.assert_called()

@pytest.mark.asyncio
async def test_add_token_with_overflow(repo, mock_session):
    # Arrange
    user_id = uuid4()
    token_hash = "new_hash"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Mock count = 5 (max_sessions default)
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 5
    mock_session.execute.side_effect = [mock_count_result, AsyncMock(), AsyncMock()] # count, delete, flush?

    # Act
    await repo.add_token(user_id, token_hash, expires_at)

    # Assert
    assert mock_session.execute.call_count >= 2 # count query and delete query
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called()

@pytest.mark.asyncio
async def test_get_token(repo, mock_session):
    # Arrange
    token_hash = "test_hash"
    expected_token = RefreshToken(token_hash=token_hash)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = expected_token
    mock_session.execute.return_value = mock_result

    # Act
    result = await repo.get_token(token_hash)

    # Assert
    assert result == expected_token
    mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_delete_token(repo, mock_session):
    # Arrange
    token_hash = "delete_me"

    # Act
    await repo.delete_token(token_hash)

    # Assert
    mock_session.execute.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_revoke_all_user_tokens(repo, mock_session):
    # Arrange
    user_id = uuid4()

    # Act
    await repo.revoke_all_user_tokens(user_id)

    # Assert
    mock_session.execute.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_commit(repo, mock_session):
    # Act
    await repo.commit()

    # Assert
    mock_session.commit.assert_called_once()
