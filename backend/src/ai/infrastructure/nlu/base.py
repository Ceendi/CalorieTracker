from abc import ABC, abstractmethod
from typing import Tuple

from src.ai.domain.models import MealExtraction


class BaseNLUExtractor(ABC):
    
    @abstractmethod
    async def extract(self, text: str) -> Tuple[MealExtraction, float]:
        pass
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        pass
