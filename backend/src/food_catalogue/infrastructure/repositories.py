import uuid
from typing import Optional, List

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.food_catalogue.domain.entities import Food, Nutrition, UnitInfo
from src.food_catalogue.infrastructure.orm_models import FoodModel, FoodUnitModel


class SqlAlchemyFoodRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: FoodModel) -> Optional[Food]:
        if model is None:
            return None

        nutrition = Nutrition(
            calories_per_100g=model.calories,
            protein_per_100g=model.protein,
            fat_per_100g=model.fat,
            carbs_per_100g=model.carbs,
        )
        
        units = []
        if model.units:
            units = [UnitInfo(unit=u.unit, grams=u.grams, label=u.label) for u in model.units]
        
        return Food(
            id=model.id,
            name=model.name,
            barcode=model.barcode,
            nutrition=nutrition,
            category=model.category,
            default_unit=model.default_unit,
            units=units,
            owner_id=model.owner_id,
            source=model.source,
        )

    async def get_by_id(self, id: uuid.UUID) -> Optional[Food]:
        stmt = select(FoodModel).where(FoodModel.id == id)
        result = await self.session.execute(stmt)
        return self._to_domain(result.scalar_one_or_none())

    async def get_by_barcode(self, barcode: str) -> Optional[Food]:
        stmt = select(FoodModel).where(FoodModel.barcode == barcode)
        result = await self.session.execute(stmt)
        return self._to_domain(result.scalar_one_or_none())

    async def search_by_name(self, query: str, limit: int = 20, owner_id: Optional[uuid.UUID] = None) -> List[Food]:
        stmt = select(FoodModel).where(
            and_(
                FoodModel.name.ilike(f"%{query}%"),
                or_(FoodModel.owner_id == owner_id, FoodModel.owner_id.is_(None)),
            )
        ).order_by(
            FoodModel.owner_id.nulls_last(),
            FoodModel.popularity_score.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save_custom_food(self, food: Food) -> Food:
        orm_units = []
        if food.units:
            orm_units = [
                FoodUnitModel(unit=u.unit, grams=u.grams, label=u.label) 
                for u in food.units
            ]
        
        model = FoodModel(
            name=food.name,
            barcode=food.barcode,
            category=food.category,
            default_unit=food.default_unit,
            units=orm_units,
            owner_id=food.owner_id,
            calories=food.nutrition.calories_per_100g,
            protein=food.nutrition.protein_per_100g,
            fat=food.nutrition.fat_per_100g,
            carbs=food.nutrition.carbs_per_100g,
            source=food.source or "user",
            popularity_score=0
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_source(self, source: str, category: Optional[str] = None, limit: int = 100) -> List[Food]:
        conditions = [FoodModel.source == source]
        
        if category:
            conditions.append(FoodModel.category.ilike(category))
        
        stmt = select(FoodModel).where(
            and_(*conditions)
        ).order_by(
            FoodModel.name
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]
