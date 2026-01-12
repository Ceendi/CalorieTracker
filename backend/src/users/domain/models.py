from fastapi_users_db_sqlalchemy import SQLAlchemyBaseOAuthAccountTableUUID, SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Float

from src.core.database import Base


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )

    verification_code: Mapped[str | None] = mapped_column(String(length=6), nullable=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(length=10), nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal: Mapped[str | None] = mapped_column(String(length=20), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(length=20), nullable=True)
