from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.infrastructure.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_token(self, user_id: UUID, token_hash: str, expires_at: datetime, max_sessions: int = 5) -> None:
        stmt_count = select(func.count()).select_from(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await self.db.execute(stmt_count)
        count = result.scalar()

        if count >= max_sessions:
            subq = (
                select(RefreshToken.id)
                .where(RefreshToken.user_id == user_id)
                .order_by(RefreshToken.created_at.asc())
                .limit(count - max_sessions + 1)
            )
            stmt_delete = delete(RefreshToken).where(RefreshToken.id.in_(subq))
            await self.db.execute(stmt_delete)

        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(token)
        await self.db.flush()

    async def get_token(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_token(self, token_hash: str) -> None:
        stmt = delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
        await self.db.execute(stmt)
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        await self.db.execute(stmt)
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()
