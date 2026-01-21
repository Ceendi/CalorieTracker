from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from starlette import status

from src.users.api.routes import current_active_user
from src.food_catalogue.api.dependencies import get_food_service
from src.food_catalogue.api.schemas import FoodOutSchema, CreateCustomFoodIn
from src.food_catalogue.application.services import FoodService
from src.food_catalogue.domain.entities import Nutrition, Food

router = APIRouter()


CATEGORIES = [
    "Cukier i słodziki",
    "Dania wegetariańskie",
    "Dania z jaj",
    "Drób",
    "Inne",
    "Mięso",
    "Mięso i drób",
    "Nabiał",
    "Nabiał i jaja",
    "Napoje",
    "Napoje roślinne",
    "Orzechy i pestki",
    "Owoce",
    "Owoce morza",
    "Pieczywo",
    "Płatki śniadaniowe",
    "Produkty wegańskie",
    "Produkty zbożowe",
    "Przyprawy",
    "Przyprawy i dodatki",
    "Rośliny strączkowe",
    "Ryby",
    "Sery",
    "Słodycze i przekąski",
    "Soki",
    "Sosy",
    "Tłuszcze",
    "Tłuszcze i oleje",
    "Warzywa",
    "Wędliny"
]


@router.get("/categories", response_model=List[str])
async def get_categories():
    return CATEGORIES


@router.get("/search", response_model=List[FoodOutSchema])
async def search(
        q: str = Query(..., min_length=1),
        user=Depends(current_active_user),
        svc: FoodService = Depends(get_food_service),
):
    results = await svc.search_food(q, user_id=user.id)
    return results


@router.get("/basic", response_model=List[FoodOutSchema])
async def get_basic_products(
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(100, ge=1, le=500, description="Maximum number of products to return"),
        svc: FoodService = Depends(get_food_service),
):
    """
    Get basic products with optional category filtering.
    Available categories can be fetched from /categories endpoint.
    """
    return await svc.get_basic_products(category=category, limit=limit)


@router.get("/barcode/{barcode}", response_model=FoodOutSchema)
async def get_product_by_barcode(
        barcode: str,
        svc: FoodService = Depends(get_food_service),
):
    food = await svc.get_by_barcode(barcode)
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not Found")
    return food


@router.post("/custom", response_model=FoodOutSchema, status_code=status.HTTP_201_CREATED)
async def create_custom_product(
        payload: CreateCustomFoodIn,
        user=Depends(current_active_user),
        svc: FoodService = Depends(get_food_service)
):
    domain_nutrition = Nutrition(
        calories_per_100g=payload.nutrition.calories_per_100g,
        protein_per_100g=payload.nutrition.protein_per_100g,
        fat_per_100g=payload.nutrition.fat_per_100g,
        carbs_per_100g=payload.nutrition.carbs_per_100g,
    )

    domain_food = Food(
        id=None,
        name=payload.name,
        barcode=payload.barcode,
        nutrition=domain_nutrition,
        owner_id=user.id,
        source="user"
    )

    saved_food = await svc.create_custom_food(domain_food, owner_id=user.id)

    return saved_food
