from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.users.api.routes import current_active_user
from src.users.domain.models import User
from src.tracking.api.dependencies import get_tracking_service
from src.tracking.api.schemas import DailyLogRead, MealEntryCreate, MealEntryUpdate
from src.tracking.application.services import TrackingService
from src.tracking.domain.exceptions import ProductNotFoundInTrackingError, MealEntryNotFoundError


router = APIRouter()


@router.post("/entries", response_model=DailyLogRead, status_code=status.HTTP_201_CREATED)
async def add_entry(
    entry_data: MealEntryCreate,
    service: TrackingService = Depends(get_tracking_service),
    user: User = Depends(current_active_user)
):
    try:
        return await service.add_meal_entry(
            user_id=user.id,
            date=entry_data.date,
            meal_type=entry_data.meal_type,
            product_id=entry_data.product_id,
            amount_grams=entry_data.amount_grams
        )
    except ProductNotFoundInTrackingError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/daily/{log_date}", response_model=DailyLogRead)
async def get_daily_log(
    log_date: date,
    service: TrackingService = Depends(get_tracking_service),
    user: User = Depends(current_active_user)
):
    log = await service.get_daily_log(user.id, log_date)
    
    if not log:
        import uuid
        return DailyLogRead(
            id=uuid.uuid4(),
            date=log_date,
            total_kcal=0,
            total_protein=0,
            total_fat=0,
            total_carbs=0,
            entries=[]
        )
    return log


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: UUID,
    service: TrackingService = Depends(get_tracking_service),
    user: User = Depends(current_active_user)
):
    try:
        await service.remove_entry(user_id=user.id, entry_id=entry_id)
    except MealEntryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_entry(
    entry_id: UUID,
    entry_data: MealEntryUpdate,
    service: TrackingService = Depends(get_tracking_service),
    user: User = Depends(current_active_user)
):
    try:
        await service.update_meal_entry(
            user_id=user.id,
            entry_id=entry_id,
            amount_grams=entry_data.amount_grams,
            meal_type=entry_data.meal_type
        )
    except MealEntryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get("/history", response_model=List[DailyLogRead])
async def get_history(
    start_date: date,
    end_date: date,
    page: int = 1,
    page_size: int = 50,
    service: TrackingService = Depends(get_tracking_service),
    user: User = Depends(current_active_user)
):
    return await service.get_history(user.id, start_date, end_date, page, page_size)
