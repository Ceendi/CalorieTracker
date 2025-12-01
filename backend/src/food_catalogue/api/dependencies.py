from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.food_catalogue.application.services import FoodService
from src.food_catalogue.infrastructure.adapters.openfoodfacts_adapter import OpenFoodFactsAdapter
from src.food_catalogue.infrastructure.repositories import SqlAlchemyFoodRepository


async def get_food_repo(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyFoodRepository:
    return SqlAlchemyFoodRepository(session)


async def get_external_adapter() -> OpenFoodFactsAdapter:
    return OpenFoodFactsAdapter()


async def get_food_service(
        repo: SqlAlchemyFoodRepository = Depends(get_food_repo),
        external: OpenFoodFactsAdapter = Depends(get_external_adapter)
) -> FoodService:
    return FoodService(repo, external)
