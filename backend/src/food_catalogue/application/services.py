import uuid
from typing import List, Optional

from src.food_catalogue.application.ports import FoodRepositoryPort, ExternalFoodProviderPort
from src.food_catalogue.domain.entities import Food


class FoodService:
    def __init__(self, repo: FoodRepositoryPort, external: ExternalFoodProviderPort):
        self.repo = repo
        self.external = external

    async def search_food(self, query: str, user_id: Optional[uuid.UUID] = None, limit: int = 20) -> List[Food]:
        results = await self.repo.search_by_name(query, limit=limit, owner_id=user_id)

        if len(results) >= limit:
            return results

        external_results = await self.external.search(query, limit=limit)

        return results + external_results

    async def get_by_barcode(self, barcode: str, user_id: Optional[uuid.UUID] = None) -> Optional[Food]:
        local = await self.repo.get_by_barcode(barcode)
        if local:
            return local

        external = await self.external.fetch_by_barcode(barcode)
        if external:
            return external

        return None

    async def get_by_id(self, food_id: str) -> Optional[Food]:
        return await self.repo.get_by_id(uuid.UUID(food_id))

    async def create_custom_food(self, food: Food, owner_id: uuid.UUID) -> Food:
        from dataclasses import replace
        food_with_owner = replace(food, owner_id=owner_id)

        saved = await self.repo.save_custom_food(food_with_owner)

        return saved

    async def get_basic_products(self, category: Optional[str] = None, limit: int = 100) -> List[Food]:
        return await self.repo.get_by_source("base_db", category=category, limit=limit)
