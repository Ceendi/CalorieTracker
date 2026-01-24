from abc import ABC, abstractmethod
from typing import Any


class BaseSTTClient(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = "pl") -> str:
        pass
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        pass

    @abstractmethod
    async def load_model(self) -> Any:
        pass
