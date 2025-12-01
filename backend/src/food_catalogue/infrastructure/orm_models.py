import uuid
from typing import Optional

from sqlalchemy import String, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column

from src.core.database import UUIDModel


class FoodModel(UUIDModel):
    __tablename__ = "foods"

    name: Mapped[str] = mapped_column(String, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)

    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user.id"), nullable=True)

    calories: Mapped[float] = mapped_column(Float, default=0.0)
    protein: Mapped[float] = mapped_column(Float, default=0.0)
    fat: Mapped[float] = mapped_column(Float, default=0.0)
    carbs: Mapped[float] = mapped_column(Float, default=0.0)

    source: Mapped[str] = mapped_column(String, default="public")

    popularity_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
