from typing import Protocol, List, Dict, Optional, Tuple

from src.ai.domain.models import (
    SearchCandidate,
    MealExtraction,
    IngredientChunk
)


class STTPort(Protocol):

    async def transcribe(self, audio_bytes: bytes, language: str = "pl") -> str:
        ...

    def is_available(self) -> bool:
        ...

    async def load_model(self) -> None:
        ...


class SearchEnginePort(Protocol):
    async def search(self, query: str, top_k: int = 20, alpha: float = 0.3) -> List[SearchCandidate]:
        ...

    def index_products(self, products: List[Dict]) -> None:
        ...

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        ...


class NLUProcessorPort(Protocol):
    def process_text(self, text: str) -> List[IngredientChunk]:
        ...

    def normalize_text(self, text: str) -> str:
        ...

    def verify_keyword_consistency(self, query: str, candidate: str) -> bool:
        ...


class NLUExtractorPort(Protocol):
    async def extract(self, text: str) -> Tuple[MealExtraction, float]:
        ...

    @classmethod
    def is_available(cls) -> bool:
        ...


class FoodSearchPort(Protocol):
    """
    Port for food search operations using pgvector hybrid search.

    This is the new interface for database-backed search, replacing
    the in-memory SearchEnginePort for production use.
    """

    async def search(
        self,
        session,
        query: str,
        limit: int = 20,
        vector_weight: float = 0.5
    ) -> List[SearchCandidate]:
        """Search for products by query text."""
        ...

    async def search_for_meal_planning(
        self,
        session,
        meal_type: str,
        preferences: Optional[Dict] = None,
        limit: int = 40
    ) -> List[Dict]:
        """Search products suitable for a meal type with optional dietary filters."""
        ...

    async def find_product_by_name(
        self,
        session,
        name: str
    ) -> Optional[Dict]:
        """Find a single product by name."""
        ...
