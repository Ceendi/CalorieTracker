from src.core.database import DBSession
from src.food_catalogue.infrastructure.repositories import SqlAlchemyFoodRepository
from src.tracking.application.services import TrackingService
from src.tracking.infrastructure.repositories import SqlAlchemyTrackingRepository


async def get_tracking_service(
    session: DBSession,
) -> TrackingService:
    tracking_repo = SqlAlchemyTrackingRepository(session)
    food_repo = SqlAlchemyFoodRepository(session)
    return TrackingService(tracking_repo, food_repo)
