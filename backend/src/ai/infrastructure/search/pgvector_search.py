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


# Maps each allergen keyword to Polish morphological stems that cover
# inflected forms (e.g. jajko → jajka/jajecznica/jajeczny).
ALLERGEN_KEYWORD_STEMS: Dict[str, List[str]] = {
    "jajko": ["jajk", "jajec", "omlet", "frittata"],
    "jaja": ["jajk", "jajec", "omlet", "frittata"],
    "jajka": ["jajk", "jajec", "omlet", "frittata"],
    "mleko": ["mleko", "mlecz", "jogurt", "kefir", "smietan", "śmietan"],
    "laktoza": ["mleko", "mlecz", "jogurt", "kefir", "smietan", "śmietan", "ser ", "serek", "twarog", "twarożk", "twarozk"],
    "gluten": ["gluten", "pszen", "żytn", "zytn", "orkisz", "owsian", "jęczmien", "jeczmien", "chleb", "bułk", "bulk", "makaron", "pierog", "nalezni", "naleśni", "kanapk", "bagiet", "tost"],
    "orzechy": ["orzech", "orzesz", "migdał", "migdal", "pistacj", "arachid"],
    "orzeszki": ["orzech", "orzesz", "migdał", "migdal", "pistacj", "arachid"],
    "ryby": ["ryb", "łosoś", "losos", "dorsz", "tuńczyk", "tunczyk", "pstrąg", "pstrag", "śledź", "sledz", "makrela"],
    "ryba": ["ryb", "łosoś", "losos", "dorsz", "tuńczyk", "tunczyk", "pstrąg", "pstrag", "śledź", "sledz", "makrela"],
    "skorupiaki": ["skorupiak", "krewet", "krab", "homar", "langust", "małż", "malz", "ostryg"],
    "soja": ["soj", "tofu", "edamame", "tempeh"],
    "seler": ["seler"],
    "gorczyca": ["gorczyc", "musztard"],
    # Frontend aliases
    "nabiał": ["mleko", "mlecz", "jogurt", "kefir", "smietan", "śmietan", "ser ", "serek", "twarog", "twarożk", "twarozk", "twaroz"],
    "nabial": ["mleko", "mlecz", "jogurt", "kefir", "smietan", "śmietan", "ser ", "serek", "twarog", "twarożk", "twarozk", "twaroz"],
    "owoce morza": ["skorupiak", "krewet", "krab", "homar", "langust", "małż", "malz", "ostryg", "osmiornic", "kalmar"],
}

# Maps allergens to food categories that should be blocked entirely.
ALLERGEN_CATEGORY_MAP: Dict[str, List[str]] = {
    "jajko": ["Dania z jaj", "Nabiał i jaja"],
    "jaja": ["Dania z jaj", "Nabiał i jaja"],
    "jajka": ["Dania z jaj", "Nabiał i jaja"],
    "mleko": ["Nabiał", "Nabiał i jaja", "Sery"],
    "nabiał": ["Nabiał", "Nabiał i jaja", "Sery"],
    "nabial": ["Nabiał", "Nabiał i jaja", "Sery"],
    "laktoza": ["Nabiał", "Nabiał i jaja", "Sery"],
    "gluten": ["Pieczywo", "Produkty zbożowe"],
    "ryby": ["Ryby", "Owoce morza"],
    "ryba": ["Ryby", "Owoce morza"],
    "skorupiaki": ["Owoce morza"],
    "owoce morza": ["Owoce morza"],
}


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
        # Format with 8 decimal places to match pgvector storage precision
        embedding_str = f"[{','.join(f'{x:.8f}' for x in query_embedding.tolist())}]"

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
        limit: int = 40,
        meal_description: Optional[str] = None,
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
            "breakfast": "sniadanie platki owsiane jajka chleb maslo ser mleko jogurt twarog banan jablko dzem miod musli kasza manna",
            "second_breakfast": "przekaska owoce jogurt kanapka banan jablko orzechy marchew ser twarog wafle ryzowe hummus papryka ogorek pomidor baton proteinowy smoothie",
            "lunch": "obiad mieso kurczak ryba ziemniaki ryz makaron warzywa zupa pomidor ogorek salata cebula marchew brokuty kalafior wolowina wieprzowina indyk fasola soczewica",
            "snack": "przekaska owoce orzechy jogurt baton jablko banan marchew ser twarog krakersy wafle ryzowe hummus rodzynki migdaly orzeszki ziemne",
            "dinner": "kolacja kanapka salata jajka ser wedlina warzywa pomidor ogorek papryka twarog chleb razowy salatka grecka omlet szynka"
        }

        base_query = MEAL_QUERIES.get(meal_type, meal_type)
        if meal_description:
            # Use only the description for FTS — specific dish name drives keyword
            # matching. Generic base_query keywords (e.g. "baton", "orzechy") would
            # overwhelm the description in FTS ranking, causing irrelevant matches.
            query = meal_description
            # Focused embedding: description + Polish meal type word only.
            meal_type_word = base_query.split()[0]
            embedding_query = f"{meal_description} {meal_type_word}"
            # Higher vector weight when description available — semantic similarity
            # captures dish intent better than keyword matching alone.
            vector_weight = 0.7
        else:
            query = base_query
            embedding_query = base_query
            vector_weight = 0.5

        # Dynamic query adjustment based on diet preferences
        # This helps RAG find relevant products even before python filtering
        if preferences:
            diet = preferences.get("diet")
            if diet == "keto":
                # Remove carb-heavy keywords and add fat/protein sources
                for kw in ["chleb", "ziemniaki", "ryz", "makaron", "banan", "jablko", "platki", "owsiane"]:
                    query = query.replace(kw, "")
                    embedding_query = embedding_query.replace(kw, "")
                query += " awokado boczek jajka oliwa orzechy mieso ryby ser maslo"
                embedding_query += " awokado oliwa orzechy"
            elif diet == "vegan":
                # Remove animal products and add plant sources
                for kw in ["jajka", "mieso", "kurczak", "ser", "wedlina", "twarog", "mleko", "maslo", "ryba", "jogurt"]:
                    query = query.replace(kw, "")
                    embedding_query = embedding_query.replace(kw, "")
                query += " tofu soczewica ciecierzyca warzywa orzechy fasola mleko_roslinne hummus"
                embedding_query += " tofu soczewica warzywa"

        # Get more results for filtering
        query_embedding = self._embedding_service.encode_query(embedding_query)
        # Format with 8 decimal places to match pgvector storage precision
        embedding_str = f"[{','.join(f'{x:.8f}' for x in query_embedding.tolist())}]"

        # Increase fetch limit drastically (limit * 10) to ensure enough valid products remain after filtering
        # This is a critical fix for "filtering by Python" issue without changing DB schema
        fetch_limit = limit * 10

        result = await session.execute(text("""
            SELECT * FROM hybrid_food_search(:query, CAST(:embedding AS vector), :limit, :weight)
        """), {
            "query": query,
            "embedding": embedding_str,
            "limit": fetch_limit,
            "weight": vector_weight,
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

    @staticmethod
    def _matches_allergen(name_lower: str, category: str, allergies: List[str]) -> bool:
        """
        Check if a product matches any declared allergen.

        Uses morphological stem matching for known allergens and falls back
        to simple substring matching for unknown ones.
        
        NOW IMPROVED: Checks if known allergens are present within user's allergy strings.
        For example "uczulenie na jajka" triggers "jajka" rules.

        Args:
            name_lower: Lowercased product name
            category: Product category string
            allergies: List of allergen keywords (lowercased)

        Returns:
            True if the product should be blocked
        """
        # 1. Identify active stems based on known allergens found in user's strings
        active_stems = []
        for known_allergen, stems in ALLERGEN_KEYWORD_STEMS.items():
            # Check if this known allergen is mentioned in any of user's allergy strings
            is_active = False
            for user_allergy in allergies:
                if known_allergen in user_allergy:
                    is_active = True
                    break
            
            if is_active:
                active_stems.extend(stems)
                
                # Check category blocking for this known allergen
                blocked_categories = ALLERGEN_CATEGORY_MAP.get(known_allergen, [])
                if category in blocked_categories:
                    return True

        # 2. Check against active stems
        for stem in active_stems:
            if stem in name_lower:
                return True

        # 3. Fallback: Check against raw user allergy strings (for unknown allergies)
        for user_allergy in allergies:
            if user_allergy in name_lower:
                return True

        return False

    def _filter_by_preferences(
        self,
        products: List[Dict],
        preferences: Dict[str, Any]
    ) -> List[Dict]:
        """
        Filter products based on dietary preferences.

        Uses morphological stem matching for allergens to handle Polish
        word forms (e.g. jajko/jajecznica/jajeczny).

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

            # Skip products containing allergens (stem-based)
            if allergies and self._matches_allergen(name_lower, category, allergies):
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
        name: str,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:
        """
        Find single best matching product by name.

        Used for exact product lookup, e.g., when matching LLM-generated
        meal plan items to database products.

        Args:
            session: Database session
            name: Product name to search for
            preferences: Optional dietary preferences for allergen filtering

        Returns:
            Dict with product info and nutrition, or None if not found
        """
        results = await self.search(session, name, limit=1, vector_weight=0.6)

        # RRF scores are low (max ~0.016), so use low threshold
        if results and results[0].score > 0.005:
            # Get full product data
            result = await session.execute(text("""
                SELECT id, name, category, calories, protein, fat, carbs
                FROM foods WHERE id = :id AND source = 'fineli'
            """), {"id": results[0].product_id})

            row = result.fetchone()
            if row:
                product = {
                    "id": str(row.id),
                    "name": row.name,
                    "category": row.category,
                    "kcal_per_100g": row.calories,
                    "protein_per_100g": row.protein,
                    "fat_per_100g": row.fat,
                    "carbs_per_100g": row.carbs
                }

                # Filter by allergens if preferences provided
                if preferences:
                    allergies = [a.lower() for a in preferences.get("allergies", [])]
                    if allergies and self._matches_allergen(
                        row.name.lower(), row.category or "", allergies
                    ):
                        logger.debug(f"Product '{row.name}' blocked by allergen filter")
                        return None

                return product

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
