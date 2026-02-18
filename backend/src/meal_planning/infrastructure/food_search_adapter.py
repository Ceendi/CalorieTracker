"""
Food search adapter for meal planning.

Implements FoodSearchPort using the existing food catalogue infrastructure.
Provides product search functionality for RAG-based ingredient selection.

.. deprecated:: 2.0.0
    This adapter uses SQL LIKE queries which provide inferior search quality
    compared to the new PgVectorSearchService. Use PgVectorSearchService from
    ``src.ai.infrastructure.search`` instead, which provides:
    - Vector similarity search via pgvector
    - Full-text search via PostgreSQL tsvector
    - Hybrid scoring with Reciprocal Rank Fusion (RRF)

Migration guide:
    Old:
        food_search = SqlAlchemyFoodSearchAdapter(session)
        products = await food_search.search_products(query)

    New:
        from src.ai.infrastructure.search import PgVectorSearchService
        from src.ai.infrastructure.embedding import get_embedding_service

        search_service = PgVectorSearchService(get_embedding_service())
        products = await search_service.search_for_meal_planning(
            session=session,
            meal_type="breakfast",
            preferences={"diet": "vegetarian"},
            limit=40
        )
"""
import warnings
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.food_catalogue.infrastructure.orm_models import FoodModel


class SqlAlchemyFoodSearchAdapter:
    """
    Food search adapter using SQLAlchemy.

    Searches the foods table for products matching a query,
    returning results in the format expected by the meal planner.

    .. deprecated:: 2.0.0
        Use PgVectorSearchService instead for better search quality.
        See module docstring for migration guide.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the adapter.

        Args:
            session: SQLAlchemy async session
        """
        warnings.warn(
            "SqlAlchemyFoodSearchAdapter is deprecated. "
            "Use PgVectorSearchService from src.ai.infrastructure.search instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._session = session

    def _create_fuzzy_regex(self, query: str) -> str:
        """
        Create a fuzzy regex pattern for Polish character matching.

        Handles Polish diacritics by creating character classes that
        match both accented and non-accented versions.

        Args:
            query: Search query

        Returns:
            Regex pattern string
        """
        import re

        replacements = {
            'a': '[aą]', 'c': '[cć]', 'e': '[eę]', 'l': '[lł]', 'n': '[nń]',
            'o': '[oó]', 's': '[sś]', 'z': '[zźż]',
            'A': '[AĄ]', 'C': '[CĆ]', 'E': '[EĘ]', 'L': '[LŁ]', 'N': '[NŃ]',
            'O': '[OÓ]', 'S': '[SŚ]', 'Z': '[ZŹŻ]'
        }

        safe_query = re.escape(query)

        pattern = ""
        for char in safe_query:
            pattern += replacements.get(char, char)

        return pattern

    def _model_to_dict(self, model: FoodModel) -> dict:
        """
        Convert FoodModel to dict for the meal planner.

        Args:
            model: FoodModel instance

        Returns:
            Dict with product info in expected format
        """
        return {
            "id": str(model.id),
            "name": model.name,
            "category": model.category,
            "kcal_per_100g": model.calories,
            "protein_per_100g": model.protein,
            "fat_per_100g": model.fat,
            "carbs_per_100g": model.carbs,
        }

    async def search_products(
        self,
        query: str,
        limit: int = 20
    ) -> List[dict]:
        """
        Search for food products by name.

        Uses fuzzy matching for Polish characters and prioritizes
        exact/prefix matches.

        Args:
            query: Search query (ingredient name or description)
            limit: Maximum number of results

        Returns:
            List of product dicts
        """
        if not query or not query.strip():
            return []

        query = query.strip()
        fuzzy_pattern = self._create_fuzzy_regex(query)

        stmt = (
            select(FoodModel)
            .where(
                or_(
                    FoodModel.name.op("~*")(fuzzy_pattern),
                    FoodModel.name.ilike(f"%{query}%"),
                )
            )
            .order_by(
                # Exact match first
                case((FoodModel.name.ilike(query), 0), else_=1),
                # Prefix match second
                case((FoodModel.name.op("~*")(f"^{fuzzy_pattern}"), 0), else_=1),
                # Prefer verified sources
                case(
                    (FoodModel.source.in_(['fineli', 'kunachowicz']), 0),
                    (FoodModel.source == 'base_db', 1),
                    else_=2
                ),
                # Shorter names (more specific) first
                func.length(FoodModel.name),
                # Then by popularity
                FoodModel.popularity_score.desc()
            )
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        products = result.scalars().all()

        logger.debug(f"Food search '{query}': found {len(products)} products")

        return [self._model_to_dict(p) for p in products]

    async def get_products_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get products by category.

        Args:
            category: Food category to filter by
            limit: Maximum number of results

        Returns:
            List of product dicts
        """
        stmt = (
            select(FoodModel)
            .where(FoodModel.category.ilike(category))
            .order_by(
                FoodModel.popularity_score.desc(),
                FoodModel.name
            )
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        products = result.scalars().all()

        return [self._model_to_dict(p) for p in products]
