"""
PgVector search adapter for voice logging integration.

This adapter wraps PgVectorSearchService to implement the SearchEnginePort
interface required by MealRecognitionService. It bridges the gap between
the session-based pgvector search and the session-less SearchEnginePort.
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from src.ai.domain.models import SearchCandidate
from src.ai.infrastructure.search.pgvector_search import PgVectorSearchService


class PgVectorSearchAdapter:
    """
    Adapter that wraps PgVectorSearchService to implement SearchEnginePort.

    This adapter is designed for use with the AudioProcessingService and
    MealRecognitionService, providing a synchronous-looking interface
    that internally uses async pgvector search.

    The adapter stores the session and provides the SearchEnginePort methods
    that MealRecognitionService expects:
    - search(query, top_k, alpha) -> List[SearchCandidate]
    - get_product_by_id(product_id) -> Optional[Dict]
    - index_products(products) -> None (no-op for pgvector, data is in DB)

    Note:
        This adapter's search() method is async, which requires updating
        MealRecognitionService to use async calls. If that's not possible,
        consider using the synchronous fallback with run_until_complete.
    """

    def __init__(
        self,
        search_service: PgVectorSearchService,
        session: AsyncSession
    ):
        """
        Initialize the adapter.

        Args:
            search_service: PgVectorSearchService instance
            session: Database session for queries
        """
        self._search_service = search_service
        self._session = session
        self._products_cache: Dict[str, Dict] = {}
        # For compatibility with old code checking this attribute
        self.embeddings = True  # Indicates search engine is ready

    async def search(
        self,
        query: str,
        top_k: int = 20,
        alpha: float = 0.3
    ) -> List[SearchCandidate]:
        """
        Search for products using pgvector hybrid search.

        Maps the SearchEnginePort interface to PgVectorSearchService.
        The alpha parameter is converted to vector_weight.

        Args:
            query: Search query (e.g., "maslo", "mleko 3.2%")
            top_k: Maximum number of results
            alpha: Balance parameter (0.0 = only FTS, 1.0 = only vector)
                  Note: This is inverted from PgVectorSearchService's vector_weight

        Returns:
            List of SearchCandidate objects sorted by relevance
        """
        # alpha maps to vector_weight: higher = more vector weight
        vector_weight = alpha

        candidates = await self._search_service.search(
            session=self._session,
            query=query,
            limit=top_k,
            vector_weight=vector_weight
        )

        # Cache product info for get_product_by_id lookups
        for candidate in candidates:
            if candidate.product_id not in self._products_cache:
                product_data = await self._fetch_product_data(candidate.product_id)
                if product_data:
                    self._products_cache[candidate.product_id] = product_data

        return candidates

    async def _fetch_product_data(self, product_id: str) -> Optional[Dict]:
        """
        Fetch full product data from database.

        Args:
            product_id: Product ID to fetch

        Returns:
            Dict with product data in format expected by MealRecognitionService
        """
        try:
            result = await self._session.execute(text("""
                SELECT
                    id, name, category, calories, protein, fat, carbs,
                    source
                FROM foods WHERE id = :id AND source IN ('fineli', 'kunachowicz')
            """), {"id": product_id})

            row = result.fetchone()
            if row:
                # Load units from food_units table
                units_result = await self._session.execute(text("""
                    SELECT label, grams FROM food_units
                    WHERE food_id = :food_id ORDER BY priority DESC
                """), {"food_id": product_id})
                units = [
                    {"name": unit_row.label, "weight_g": unit_row.grams}
                    for unit_row in units_result.fetchall()
                ]

                return {
                    "id": str(row.id),
                    "name_pl": row.name,
                    "name_en": "",  # Not available in current schema
                    "category": row.category or "UNKNOWN",
                    "kcal_100g": row.calories or 0,
                    "protein_100g": row.protein or 0,
                    "fat_100g": row.fat or 0,
                    "carbs_100g": row.carbs or 0,
                    "source": row.source,
                    "units": units
                }
        except Exception as e:
            logger.error(f"Failed to fetch product {product_id}: {e}")

        return None

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """
        Get product data by ID from cache.

        Note: This is synchronous for SearchEnginePort compatibility.
        Products are cached during search() calls.

        Args:
            product_id: Product ID to look up

        Returns:
            Product dict or None if not in cache
        """
        return self._products_cache.get(str(product_id))

    def index_products(self, products: List[Dict]) -> None:
        """
        No-op for pgvector adapter.

        Product embeddings are stored in the database and indexed there.
        This method exists for SearchEnginePort interface compatibility.

        Args:
            products: List of products (ignored)
        """
        logger.info(
            "index_products called on PgVectorSearchAdapter - "
            "no action needed, products are indexed in PostgreSQL"
        )

    @property
    def products(self) -> List[Dict]:
        """Return empty list for compatibility."""
        return []

    @property
    def products_by_id(self) -> Dict[str, Dict]:
        """Return the products cache."""
        return self._products_cache
