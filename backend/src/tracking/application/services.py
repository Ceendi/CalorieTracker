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
        amount_grams: float,
        unit_label: Optional[str] = None,
        unit_grams: Optional[float] = None,
        unit_quantity: Optional[float] = None
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
            unit_label=unit_label,
            unit_grams=unit_grams,
            unit_quantity=unit_quantity,
            kcal_per_100g=int(product.nutrition.calories_per_100g),
            prot_per_100g=product.nutrition.protein_per_100g,
            fat_per_100g=product.nutrition.fat_per_100g,
            carb_per_100g=product.nutrition.carbs_per_100g
        )
        
        await self.tracking_repo.add_entry(user_id, entry_domain)
        await self.tracking_repo.recalculate_totals(daily_log.id)
        await self.tracking_repo.commit() 
        
        return await self.tracking_repo.get_daily_log(user_id, log_date)

    async def add_meal_entries_bulk(
        self,
        user_id: uuid.UUID,
        log_date: date,
        meal_type: MealType,
        items: List[dict]
    ) -> DailyLog:
        if not items:
            raise ValueError("At least one item is required")

        daily_log = await self.tracking_repo.get_or_create_daily_log(user_id, log_date)
        entries_to_add = []

        try:
            for item_data in items:
                product_id = item_data['product_id']
                product = await self.food_repo.get_by_id(product_id)
                if not product:
                    raise ProductNotFoundInTrackingError(str(product_id))

                entry_domain = MealEntry(
                    id=uuid.uuid4(),
                    daily_log_id=daily_log.id,
                    meal_type=meal_type,
                    product_id=product.id,
                    product_name=product.name,
                    amount_grams=item_data['amount_grams'],
                    unit_label=item_data.get('unit_label'),
                    unit_grams=item_data.get('unit_grams'),
                    unit_quantity=item_data.get('unit_quantity'),
                    kcal_per_100g=int(product.nutrition.calories_per_100g),
                    prot_per_100g=product.nutrition.protein_per_100g,
                    fat_per_100g=product.nutrition.fat_per_100g,
                    carb_per_100g=product.nutrition.carbs_per_100g
                )
                entries_to_add.append(entry_domain)

            await self.tracking_repo.add_entries_bulk(user_id, entries_to_add)
            await self.tracking_repo.recalculate_totals(daily_log.id)
            await self.tracking_repo.commit()
            
            return await self.tracking_repo.get_daily_log(user_id, log_date)
            
        except Exception as e:
            # SQLAlchemy AsyncSession rollback is usually handled by the context manager 
            # or explicitly if we managed it. Since we are calling commit() manually in other methods,
            # we should also handle exception here if we want explicit rollback or just let it propagate.
            # In FastAPI it's often handled in middleware if it fails.
            raise e

    async def get_daily_log(self, user_id: uuid.UUID, log_date: date) -> Optional[DailyLog]:
        return await self.tracking_repo.get_daily_log(user_id, log_date)

    async def remove_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        entry = await self.tracking_repo.get_entry(entry_id, user_id)
        if not entry:
            raise MealEntryNotFoundError(str(entry_id))
        daily_log_id = entry.daily_log_id
        
        result = await self.tracking_repo.delete_entry(entry_id, user_id)
        if not result:
            raise MealEntryNotFoundError(str(entry_id))
        await self.tracking_repo.recalculate_totals(daily_log_id)
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
            await self.tracking_repo.recalculate_totals(entry.daily_log_id)
            await self.tracking_repo.commit()

    async def get_history(self, user_id: uuid.UUID, start_date: date, end_date: date, page: int = 1,
                          page_size: int = 50) -> List[DailyLog]:
        return await self.tracking_repo.get_history(user_id, start_date, end_date, page, page_size)
