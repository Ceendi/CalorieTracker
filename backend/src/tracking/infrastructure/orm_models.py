import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import UUIDModel


class TrackingDailyLog(UUIDModel):
    __tablename__ = "tracking_daily_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    total_kcal: Mapped[int] = mapped_column(Integer, default=0)
    total_protein: Mapped[float] = mapped_column(Float, default=0.0)
    total_fat: Mapped[float] = mapped_column(Float, default=0.0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0.0)

    entries: Mapped[List["TrackingMealEntry"]] = relationship(
        "TrackingMealEntry", 
        back_populates="daily_log", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uix_user_date"),
    )


class TrackingMealEntry(UUIDModel):
    __tablename__ = "tracking_meal_entries"

    daily_log_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracking_daily_logs.id"), nullable=False, index=True)
    
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("foods.id"), nullable=True)
    
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    meal_type: Mapped[str] = mapped_column(String, nullable=False)
    
    amount_grams: Mapped[float] = mapped_column(Float, nullable=False)
    
    kcal_per_100g: Mapped[int] = mapped_column(Integer, nullable=False)
    prot_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carb_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    
    daily_log: Mapped["TrackingDailyLog"] = relationship("TrackingDailyLog", back_populates="entries")
