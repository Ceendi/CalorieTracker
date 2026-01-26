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
    def search(self, query: str, top_k: int = 20, alpha: float = 0.3) -> List[SearchCandidate]:
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
