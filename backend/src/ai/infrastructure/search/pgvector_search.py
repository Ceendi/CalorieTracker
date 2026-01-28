"""
PgVector-based hybrid search service combining vector similarity and full-text search.

Uses pgvector for vector operations and tsvector for PostgreSQL full-text search.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from src.ai.infrastructure.embedding.embedding_service import EmbeddingService
from src.ai.domain.models import SearchCandidate


class PgVectorSearchService:
    """
    Hybrid search using pgvector + PostgreSQL FTS.

    Combines:
    - Vector similarity search (cosine distance) via pgvector
    - Full-text search (tsvector/tsquery) via PostgreSQL
    - Reciprocal Rank Fusion (RRF) for score combination
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize the search service.

        Args:
            embedding_service: Optional EmbeddingService instance.
                              If not provided, creates a singleton instance.
        """
        self._embedding_service = embedding_service or EmbeddingService()

    async def search(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 20,
        vector_weight: float = 0.5
    ) -> List[SearchCandidate]:
        """
        Hybrid search combining vector similarity and full-text search.

        Args:
            session: Database session
            query: Search query (e.g., "maslo", "mleko 3.2%")
            limit: Max results
            vector_weight: 0.0 = only FTS, 1.0 = only vector, 0.5 = balanced

        Returns:
            List of SearchCandidate sorted by relevance
        """
        # 1. Encode query to embedding
        query_embedding = self._embedding_service.encode_query(query)
        embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"

        # 2. Call hybrid search function
        result = await session.execute(text("""
            SELECT * FROM hybrid_food_search(:query, CAST(:embedding AS vector), :limit, :weight)
        """), {
            "query": query,
            "embedding": embedding_str,
            "limit": limit,
            "weight": vector_weight
        })

        rows = result.fetchall()

        # 3. Map to SearchCandidate
        candidates = []
        for row in rows:
            candidates.append(SearchCandidate(
                product_id=str(row.id),
                name=row.name,
                category=row.category or "UNKNOWN",
                score=float(row.score),
                passed_guard=True,
                notes=f"pgvector_hybrid(w={vector_weight})"
            ))

        logger.debug(f"Search '{query}': found {len(candidates)} results")
        return candidates

    async def search_for_meal_planning(
        self,
        session: AsyncSession,
        meal_type: str,
        preferences: Optional[Dict[str, Any]] = None,
        limit: int = 40
    ) -> List[Dict]:
        """
        Search products for meal planning.

        Returns full nutrition data for LLM context. This method is designed
        to provide rich product information for the meal planning module.

        Args:
            session: Database session
            meal_type: Type of meal (breakfast, lunch, dinner, snack, second_breakfast)
            preferences: Optional dietary preferences dict with keys:
                        - allergies: List[str] - ingredients to avoid
                        - diet: str - "vegetarian", "vegan", etc.
                        - excluded_ingredients: List[str] - specific exclusions
            limit: Maximum number of products to return

        Returns:
            List of dicts with product info and nutrition data
        """
        MEAL_QUERIES = {
            "breakfast": "sniadanie platki owsiane jajka chleb maslo ser mleko jogurt twarog banan",
            "second_breakfast": "przekaska owoce jogurt kanapka banan jablko orzechy marchew",
            "lunch": "obiad mieso kurczak ryba ziemniaki ryz makaron warzywa zupa pomidor ogorek salata cebula",
            "snack": "przekaska owoce orzechy jogurt baton jablko banan marchew",
            "dinner": "kolacja kanapka salata jajka ser wedlina warzywa pomidor ogorek papryka"
        }

        query = MEAL_QUERIES.get(meal_type, meal_type)

        # Get more results for filtering
        query_embedding = self._embedding_service.encode_query(query)
        embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"

        result = await session.execute(text("""
            SELECT * FROM hybrid_food_search(:query, CAST(:embedding AS vector), :limit, 0.5)
        """), {
            "query": query,
            "embedding": embedding_str,
            "limit": limit * 2  # Get extra for filtering
        })

        rows = result.fetchall()

        # Convert to dicts with nutrition
        products = []
        for row in rows:
            products.append({
                "id": str(row.id),
                "name": row.name,
                "category": row.category,
                "kcal_per_100g": row.calories,
                "protein_per_100g": row.protein,
                "fat_per_100g": row.fat,
                "carbs_per_100g": row.carbs,
                "score": float(row.score)
            })

        # Filter by preferences if provided
        if preferences:
            products = self._filter_by_preferences(products, preferences)

        return products[:limit]

    def _filter_by_preferences(
        self,
        products: List[Dict],
        preferences: Dict[str, Any]
    ) -> List[Dict]:
        """
        Filter products based on dietary preferences.

        Args:
            products: List of product dicts
            preferences: Dietary preferences containing:
                        - allergies: ingredients to avoid
                        - diet: vegetarian/vegan/etc
                        - excluded_ingredients: specific exclusions

        Returns:
            Filtered list of products
        """
        filtered = []

        allergies = [a.lower() for a in preferences.get("allergies", [])]
        diet = preferences.get("diet")
        excluded = [e.lower() for e in preferences.get("excluded_ingredients", [])]

        # Polish category names for meat and animal products
        meat_categories = [
            "Mieso", "Drob", "Mieso i drob", "Ryby", "Owoce morza", "Wedliny"
        ]
        animal_categories = meat_categories + [
            "Nabial", "Nabial i jaja", "Sery", "Dania z jaj"
        ]

        for p in products:
            name_lower = p["name"].lower()
            category = p.get("category", "")

            # Skip products containing allergens
            if any(a in name_lower for a in allergies):
                continue

            # Skip excluded ingredients
            if any(e in name_lower for e in excluded):
                continue

            # Apply diet restrictions
            if diet == "vegetarian" and category in meat_categories:
                continue
            if diet == "vegan" and category in animal_categories:
                continue

            filtered.append(p)

        return filtered

    async def find_product_by_name(
        self,
        session: AsyncSession,
        name: str
    ) -> Optional[Dict]:
        """
        Find single best matching product by name.

        Used for exact product lookup, e.g., when matching LLM-generated
        meal plan items to database products.

        Args:
            session: Database session
            name: Product name to search for

        Returns:
            Dict with product info and nutrition, or None if not found
        """
        results = await self.search(session, name, limit=1, vector_weight=0.6)

        if results and results[0].score > 0.3:
            # Get full product data
            result = await session.execute(text("""
                SELECT id, name, category, calories, protein, fat, carbs
                FROM foods WHERE id = :id AND source = 'fineli'
            """), {"id": results[0].product_id})

            row = result.fetchone()
            if row:
                return {
                    "id": str(row.id),
                    "name": row.name,
                    "category": row.category,
                    "kcal_per_100g": row.calories,
                    "protein_per_100g": row.protein,
                    "fat_per_100g": row.fat,
                    "carbs_per_100g": row.carbs
                }

        return None

    async def search_by_category(
        self,
        session: AsyncSession,
        category: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search products by category name.

        Args:
            session: Database session
            category: Category name (e.g., "Nabial", "Owoce")
            limit: Maximum results

        Returns:
            List of product dicts from the specified category
        """
        result = await session.execute(text("""
            SELECT id, name, category, calories, protein, fat, carbs
            FROM foods
            WHERE category ILIKE :category AND source = 'fineli'
            LIMIT :limit
        """), {
            "category": f"%{category}%",
            "limit": limit
        })

        rows = result.fetchall()
        products = []
        for row in rows:
            products.append({
                "id": str(row.id),
                "name": row.name,
                "category": row.category,
                "kcal_per_100g": row.calories,
                "protein_per_100g": row.protein,
                "fat_per_100g": row.fat,
                "carbs_per_100g": row.carbs
            })

        return products
