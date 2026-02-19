import uuid
from typing import Optional, List

from sqlalchemy import String, ForeignKey, Float, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from src.core.database import UUIDModel
from src.food_catalogue.domain.enums import UnitType, UnitLabel


class FoodModel(UUIDModel):
    __tablename__ = "foods"

    name: Mapped[str] = mapped_column(String, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    default_unit: Mapped[str] = mapped_column(String, default="gram")
    
    units: Mapped[List["FoodUnitModel"]] = relationship(
        "FoodUnitModel", 
        back_populates="food", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user.id"), nullable=True)

    calories: Mapped[float] = mapped_column(Float, default=0.0)
    protein: Mapped[float] = mapped_column(Float, default=0.0)
    fat: Mapped[float] = mapped_column(Float, default=0.0)
    carbs: Mapped[float] = mapped_column(Float, default=0.0)

    source: Mapped[str] = mapped_column(String, default="public")

    popularity_score: Mapped[int] = mapped_column(Integer, default=0, index=True)

    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384), nullable=True)


class FoodUnitModel(UUIDModel):
    __tablename__ = "food_units"

    food_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), 
        index=True
    )
    food: Mapped["FoodModel"] = relationship("FoodModel", back_populates="units")
    
    unit: Mapped[UnitType] = mapped_column(SAEnum(UnitType, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]))
    grams: Mapped[float] = mapped_column(Float)
    label: Mapped[UnitLabel] = mapped_column(SAEnum(UnitLabel, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]))
    
    priority: Mapped[int] = mapped_column(Integer, default=0)
