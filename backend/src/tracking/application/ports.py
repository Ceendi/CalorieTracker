import uuid
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from src.tracking.domain.entities import DailyLog, MealEntry


class TrackingRepositoryPort(ABC):
    @abstractmethod
    async def get_daily_log(self, user_id: uuid.UUID, log_date: date) -> Optional[DailyLog]:
        pass

    @abstractmethod
    async def get_or_create_daily_log(self, user_id: uuid.UUID, log_date: date) -> DailyLog:
        pass

    @abstractmethod
    async def add_entry(self, user_id: uuid.UUID, entry: MealEntry) -> None:
        pass

    @abstractmethod
    async def delete_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def get_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> Optional[MealEntry]:
        pass

    @abstractmethod
    async def update_entry(self, entry: MealEntry) -> None:
        pass

    @abstractmethod
    async def get_history(self, user_id: uuid.UUID, start_date: date, end_date: date, page: int, page_size: int) \
            -> List[DailyLog]:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def recalculate_totals(self, daily_log_id: uuid.UUID) -> None:
        pass
