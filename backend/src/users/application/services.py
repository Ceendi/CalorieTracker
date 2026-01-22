import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import HTTPException, status
from fastapi_users import BaseUserManager
from fastapi_users.authentication import Strategy

from src.core.config import settings
from src.users.domain.models import User
from src.users.infrastructure.models import RefreshToken
from src.users.infrastructure.repositories import RefreshTokenRepository


class AuthService:
    def __init__(self, refresh_token_repo: RefreshTokenRepository):
        self.repo = refresh_token_repo

    def _generate_refresh_token(self) -> str:
        return secrets.token_urlsafe(64)

    async def create_tokens(self, user: User, strategy: Strategy) -> Dict[str, Any]:
        access_token = await strategy.write_token(user)

        refresh_token = self._generate_refresh_token()
        refresh_token_hash = RefreshToken.hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.repo.add_token(user.id, refresh_token_hash, expires_at)
        await self.repo.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }

    async def refresh_session(self, refresh_token: str, strategy: Strategy, user_manager: BaseUserManager) \
            -> Dict[str, Any]:
        token_hash = RefreshToken.hash_token(refresh_token)

        db_token = await self.repo.get_token(token_hash)
        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if db_token.expires_at < datetime.now(timezone.utc):
            await self.repo.delete_token(token_hash)
            await self.repo.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        user = await user_manager.get(db_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

        await self.repo.delete_token(token_hash)

        return await self.create_tokens(user, strategy)

    async def logout(self, refresh_token: str) -> None:
        token_hash = RefreshToken.hash_token(refresh_token)
        await self.repo.delete_token(token_hash)
        await self.repo.commit()
