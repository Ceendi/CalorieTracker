from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.users.application.services import AuthService
from src.users.infrastructure.repositories import RefreshTokenRepository

async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    repo = RefreshTokenRepository(db)
    return AuthService(repo)
