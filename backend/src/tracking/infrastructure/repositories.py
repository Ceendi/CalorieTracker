from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.tracking.application.ports import TrackingRepositoryPort
from src.tracking.domain.entities import DailyLog, MealEntry, MealType
from src.tracking.infrastructure.orm_models import TrackingDailyLog, TrackingMealEntry


class SqlAlchemyTrackingRepository(TrackingRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_log(self, user_id: UUID, log_date: date) -> Optional[DailyLog]:
        stmt = (
            select(TrackingDailyLog)
            .where(
                and_(
                    TrackingDailyLog.user_id == user_id,
                    TrackingDailyLog.date == log_date
                )
            )
            .options(selectinload(TrackingDailyLog.entries))
        )
        
        result = await self.db.execute(stmt)
        orm_daily_log = result.scalar_one_or_none()
        
        if not orm_daily_log:
            return None
            
        return self._to_domain(orm_daily_log)

    async def get_or_create_daily_log(self, user_id: UUID, log_date: date) -> DailyLog:
        stmt = select(TrackingDailyLog).where(
            and_(
                TrackingDailyLog.user_id == user_id,
                TrackingDailyLog.date == log_date
            )
        ).options(selectinload(TrackingDailyLog.entries))
        
        result = await self.db.execute(stmt)
        daily_log = result.scalar_one_or_none()
        
        if not daily_log:
            daily_log = TrackingDailyLog(
                user_id=user_id,
                date=log_date,
                total_kcal=0,
                total_protein=0,
                total_fat=0,
                total_carbs=0
            )
            self.db.add(daily_log)
            await self.db.flush() 
        
        return self._to_domain(daily_log)

    async def add_entry(self, user_id: UUID, entry: MealEntry) -> None:
        orm_entry = TrackingMealEntry(
            id=entry.id,
            daily_log_id=entry.daily_log_id,
            product_id=entry.product_id,
            product_name=entry.product_name,
            meal_type=entry.meal_type.value,
            amount_grams=entry.amount_grams,
            kcal_per_100g=entry.kcal_per_100g,
            prot_per_100g=entry.prot_per_100g,
            fat_per_100g=entry.fat_per_100g,
            carb_per_100g=entry.carb_per_100g
        )
        self.db.add(orm_entry)
        await self.db.flush()

    async def delete_entry(self, entry_id: UUID, user_id: UUID) -> bool:
        stmt = select(TrackingMealEntry).join(TrackingDailyLog).where(
            and_(
                TrackingMealEntry.id == entry_id,
                TrackingDailyLog.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if entry:
            await self.db.delete(entry)
            return True
        return False

    async def get_entry(self, entry_id: UUID, user_id: UUID) -> Optional[MealEntry]:
        stmt = (
            select(TrackingMealEntry)
            .join(TrackingDailyLog)
            .where(
                and_(
                    TrackingMealEntry.id == entry_id,
                    TrackingDailyLog.user_id == user_id
                )
            )
        )
        result = await self.db.execute(stmt)
        orm_entry = result.scalar_one_or_none()
        
        if not orm_entry:
            return None
            
        return MealEntry(
            id=orm_entry.id,
            daily_log_id=orm_entry.daily_log_id,
            meal_type=MealType(orm_entry.meal_type),
            product_id=orm_entry.product_id,
            product_name=orm_entry.product_name,
            amount_grams=orm_entry.amount_grams,
            kcal_per_100g=orm_entry.kcal_per_100g,
            prot_per_100g=orm_entry.prot_per_100g,
            fat_per_100g=orm_entry.fat_per_100g,
            carb_per_100g=orm_entry.carb_per_100g
        )

    async def update_entry(self, entry: MealEntry) -> None:
        stmt = (
            select(TrackingMealEntry)
            .where(TrackingMealEntry.id == entry.id)
        )
        result = await self.db.execute(stmt)
        orm_entry = result.scalar_one_or_none()
        
        if orm_entry:
            orm_entry.amount_grams = entry.amount_grams
            orm_entry.meal_type = entry.meal_type.value
            await self.db.flush()

    async def get_history(self, user_id: UUID, start_date: date, end_date: date, page: int = 1, page_size: int = 50) -> List[DailyLog]:
        offset = (page - 1) * page_size
        stmt = (
            select(TrackingDailyLog)
            .where(
                and_(
                    TrackingDailyLog.user_id == user_id,
                    TrackingDailyLog.date >= start_date,
                    TrackingDailyLog.date <= end_date
                )
            )
            .options(selectinload(TrackingDailyLog.entries))
            .order_by(desc(TrackingDailyLog.date))
            .limit(page_size)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        return [self._to_domain(log) for log in result.scalars().all()]

    async def commit(self) -> None:
        await self.db.commit()

    def _to_domain(self, orm_log: TrackingDailyLog) -> DailyLog:
        return DailyLog(
            id=orm_log.id,
            user_id=orm_log.user_id,
            date=orm_log.date,
            entries=[
                MealEntry(
                    id=e.id,
                    daily_log_id=e.daily_log_id,
                    meal_type=MealType(e.meal_type),
                    product_id=e.product_id,
                    product_name=e.product_name,
                    amount_grams=e.amount_grams,
                    kcal_per_100g=e.kcal_per_100g,
                    prot_per_100g=e.prot_per_100g,
                    fat_per_100g=e.fat_per_100g,
                    carb_per_100g=e.carb_per_100g
                )
                for e in orm_log.entries
            ]
        )
