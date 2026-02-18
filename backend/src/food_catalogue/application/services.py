import uuid
from typing import List, Optional
from dataclasses import replace
from loguru import logger

from src.food_catalogue.application.ports import FoodRepositoryPort, ExternalFoodProviderPort
from src.food_catalogue.domain.entities import Food


class FoodService:
    def __init__(self, repo: FoodRepositoryPort, external: ExternalFoodProviderPort):
        self.repo = repo
        self.external = external

    async def search_food(self, query: str, user_id: Optional[uuid.UUID] = None, limit: int = 20) -> List[Food]:
        # 1. Search local DB first
        results = await self.repo.search_by_name(query, limit=limit, owner_id=user_id)

        if len(results) >= limit:
            return results

        # 2. If not enough results, search external provider
        try:
            external_results = await self.external.search(query, limit=limit)
        except Exception as e:
            logger.error(f"External search failed for query '{query}': {e}")
            return results

        # 3. Persist new external products to ensure they have valid UUIDs in our system
        ready_external_products = []
        for food in external_results:
            if food.id and isinstance(food.id, uuid.UUID):
                ready_external_products.append(food)
            else:
                persisted = await self._persist_external_product(food)
                if persisted:
                    ready_external_products.append(persisted)

        local_ids = {f.id for f in results}
        unique_external = [f for f in ready_external_products if f.id not in local_ids]
        return results + unique_external

    async def _persist_external_product(self, food: Food) -> Optional[Food]:
        """
        Persists an external product to the local database to generate a stable UUID.
        Handles duplicates by checking if the product already exists by barcode.
        """
        try:
            if food.barcode:
                existing = await self.repo.get_by_barcode(food.barcode)
                if existing:
                    return existing

            food_to_save = replace(food, id=None, source="openfoodfacts")
            
            return await self.repo.save_custom_food(food_to_save)

        except Exception as e:
            logger.warning(f"Failed to persist external food '{food.name}' (barcode: {food.barcode}): {e}")
            return None

    async def get_by_barcode(self, barcode: str, user_id: Optional[uuid.UUID] = None) -> Optional[Food]:
        local = await self.repo.get_by_barcode(barcode)
        if local:
            return local

        external = await self.external.fetch_by_barcode(barcode)
        if external:
            # Auto-persist single product lookup as well
            return await self._persist_external_product(external)

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
