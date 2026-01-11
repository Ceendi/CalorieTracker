import uuid
from datetime import date
from typing import List, Optional

from src.food_catalogue.application.ports import FoodRepositoryPort
from src.tracking.application.ports import TrackingRepositoryPort
from src.tracking.domain.entities import DailyLog, MealEntry, MealType
from src.tracking.domain.exceptions import ProductNotFoundInTrackingError, MealEntryNotFoundError


class TrackingService:
    def __init__(self, tracking_repo: TrackingRepositoryPort, food_repo: FoodRepositoryPort):
        self.tracking_repo = tracking_repo
        self.food_repo = food_repo

    async def add_meal_entry(
        self,
        user_id: uuid.UUID,
        log_date: date,
        meal_type: MealType,
        product_id: uuid.UUID,
        amount_grams: float
    ) -> DailyLog:
        product = await self.food_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundInTrackingError(str(product_id))
            
        daily_log = await self.tracking_repo.get_or_create_daily_log(user_id, log_date)
        
        new_entry_id = uuid.uuid4()
        entry_domain = MealEntry(
            id=new_entry_id,
            daily_log_id=daily_log.id,
            meal_type=meal_type,
            product_id=product.id,
            product_name=product.name,
            amount_grams=amount_grams,
            kcal_per_100g=int(product.nutrition.calories_per_100g),
            prot_per_100g=product.nutrition.protein_per_100g,
            fat_per_100g=product.nutrition.fat_per_100g,
            carb_per_100g=product.nutrition.carbs_per_100g
        )
        
        await self.tracking_repo.add_entry(user_id, entry_domain)
        await self.tracking_repo.commit() 
        
        return await self.tracking_repo.get_daily_log(user_id, log_date)

    async def get_daily_log(self, user_id: uuid.UUID, log_date: date) -> Optional[DailyLog]:
        return await self.tracking_repo.get_daily_log(user_id, log_date)

    async def remove_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        result = await self.tracking_repo.delete_entry(entry_id, user_id)
        if not result:
            raise MealEntryNotFoundError(str(entry_id))
        await self.tracking_repo.commit()

    async def update_meal_entry(
        self,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
        amount_grams: Optional[float] = None,
        meal_type: Optional[MealType] = None
    ) -> None:
        entry = await self.tracking_repo.get_entry(entry_id, user_id)
        if not entry:
            raise MealEntryNotFoundError(str(entry_id))
        
        updated = False
        if amount_grams is not None:
            entry.amount_grams = amount_grams
            updated = True
            
        if meal_type is not None:
            entry.meal_type = meal_type
            updated = True
            
        if updated:
            await self.tracking_repo.update_entry(entry)
            await self.tracking_repo.commit()

    async def get_history(self, user_id: uuid.UUID, start_date: date, end_date: date, page: int = 1,
                          page_size: int = 50) -> List[DailyLog]:
        return await self.tracking_repo.get_history(user_id, start_date, end_date, page, page_size)
