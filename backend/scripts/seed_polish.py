"""
Seed Polish Products to Database
=================================
Seeds the polish_products.json into the foods and food_units tables.
Adds ~441 Polish food products missing from the Fineli database.

Source: Kunachowicz et al. — Tabele składu i wartości odżywczej żywności (PZWL)

Usage:
    cd backend
    uv run python scripts/seed_polish.py
"""

import asyncio
import json
import sys
import os
from uuid import uuid4
from pathlib import Path
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "seeds" / "polish_products.json"

CATEGORY_MAP = {
    # Dairy & cheese
    "DAIRY": "Nabiał",
    "CHEESE": "Sery",
    # Meat & fish products
    "DELI": "Wędliny",
    "FISH_PRODUCT": "Ryby przetworzone",
    # Grains & bread
    "FLOUR": "Mąki",
    "GRAIN": "Produkty zbożowe",
    "PASTA": "Produkty zbożowe",
    "RICE": "Produkty zbożowe",
    "CEREAL": "Płatki i musli",
    "BREAD": "Pieczywo",
    # Vegetables & mushrooms
    "POTATO": "Ziemniaki i skrobie",
    "MUSHROOM": "Grzyby",
    # Fruits & preserves
    "DRIED_FRUIT": "Owoce suszone",
    "JAM": "Dżemy i przetwory",
    # Nuts & seeds
    "NUTS": "Orzechy i nasiona",
    "SEEDS": "Orzechy i nasiona",
    # Sweets & snacks
    "CHOCOLATE": "Słodycze",
    "COOKIE": "Ciastka i herbatniki",
    "CAKE": "Ciasta",
    "SWEETS": "Słodycze",
    "CHIP": "Przekąski",
    "SNACKS": "Przekąski",
    # Beverages
    "BEVERAGE": "Napoje",
    # Condiments
    "CONDIMENT": "Sosy i dodatki",
    # Prepared dishes
    "SOUP": "Zupy",
    "MILK_DISH": "Dania mleczne",
    "FISH_DISH": "Dania rybne",
    "MEAT_DISH": "Dania mięsne",
    "DUMPLING": "Pierogi i kluski",
    "SALAD": "Surówki i sałatki",
    "EGG_DISH": "Dania jajeczne",
    "DESSERT": "Desery",
    "POLISH_DISH": "Dania polskie",
    "ICE_CREAM": "Lody",
}

UNIT_MAP = {
    "Sztuka": ("piece", "sztuka"),
    "Sztuka (mała)": ("piece", "Sztuka (mała)"),
    "Sztuka (średnia)": ("piece", "Sztuka (średnia)"),
    "Sztuka (duża)": ("piece", "Sztuka (duża)"),
    "Łyżka": ("tablespoon", "łyżka"),
    "Łyżeczka": ("teaspoon", "łyżeczka"),
    "Szklanka": ("cup", "szklanka"),
    "Porcja": ("portion", "porcja"),
    "Porcja (mała)": ("portion", "Porcja (mała)"),
    "Porcja (średnia)": ("portion", "Porcja (średnia)"),
    "Porcja (duża)": ("portion", "Porcja (duża)"),
}


def guess_unit_type(name: str) -> tuple[str, str]:
    """Map a free-form unit name to a valid (UnitType, UnitLabel) pair.

    Only returns values that exist in the UnitType/UnitLabel enums to avoid
    SQLAlchemy enum lookup errors at query time.
    """
    n = name.lower()
    if "kromka" in n:
        return "piece", "kromka"
    if "plasterki" in n or "plasterek" in n:
        return "piece", "plasterki"
    if "plaster" in n:
        return "piece", "plaster"
    if "szklanka" in n:
        return "cup", "szklanka"
    if "łyżeczka" in n:
        return "teaspoon", "łyżeczka"
    if "łyżka" in n:
        return "tablespoon", "łyżka"
    if "tabliczka" in n:
        return "piece", "tabliczka"
    if "częstka" in n:
        return "piece", "sztuka"
    if "sztuk" in n:
        return "piece", "sztuka"
    if "opakowanie" in n or "słoik" in n:
        return "portion", "opakowanie"
    if "trójkątne" in n:
        return "portion", "opakowanie"
    if "porcja" in n:
        return "portion", "porcja"
    if any(w in n for w in ["mały", "mała"]):
        return "piece", "Sztuka (mała)"
    if any(w in n for w in ["średni", "średnia"]):
        return "piece", "Sztuka (średnia)"
    if any(w in n for w in ["duży", "duża"]):
        return "piece", "Sztuka (duża)"
    # Default
    return "piece", "sztuka"


async def seed_polish():
    logger.info("Starting Polish products seeding...")

    if not DATA_PATH.exists():
        logger.error(f"File {DATA_PATH} not found!")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        products = data.get("products", [])

    logger.info(f"Loaded {len(products)} products from JSON.")

    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        counter = 0
        skipped = 0
        replaced = 0
        units_counter = 0

        for p in products:
            name = p.get("name_pl") or p.get("name_en", "Unknown")

            # Check for duplicate by name
            result = await session.execute(
                text("SELECT id, source FROM foods WHERE name = :name"),
                {"name": name},
            )
            existing = result.fetchone()
            if existing:
                existing_id, existing_source = existing
                if existing_source == "openfoodfacts":
                    # Replace OpenFoodFacts with Kunachowicz (more reliable)
                    cat_code = p.get("category", "POLISH_DISH")
                    category_pl = CATEGORY_MAP.get(cat_code, "Inne")
                    await session.execute(
                        text("DELETE FROM food_units WHERE food_id = :fid"),
                        {"fid": str(existing_id)},
                    )
                    await session.execute(
                        text("""
                            UPDATE foods SET category = :category, calories = :calories,
                            protein = :protein, fat = :fat, carbs = :carbs,
                            source = :source, embedding = NULL
                            WHERE id = :id
                        """),
                        {
                            "id": str(existing_id),
                            "category": category_pl,
                            "calories": p.get("kcal_100g", 0),
                            "protein": p.get("protein_100g", 0),
                            "fat": p.get("fat_100g", 0),
                            "carbs": p.get("carbs_100g", 0),
                            "source": "kunachowicz",
                        },
                    )
                    food_id = existing_id
                    replaced += 1
                    logger.info(f"Replaced openfoodfacts: {name}")
                else:
                    # Refresh units from JSON even for existing kunachowicz products
                    await session.execute(
                        text("DELETE FROM food_units WHERE food_id = :fid"),
                        {"fid": str(existing_id)},
                    )
                    food_id = existing_id
                    skipped += 1
                    logger.info(f"Refreshing units for existing ({existing_source}): {name}")
            else:
                food_id = uuid4()
                cat_code = p.get("category", "POLISH_DISH")
                category_pl = CATEGORY_MAP.get(cat_code, "Inne")

                await session.execute(
                    text("""
                        INSERT INTO foods (id, name, category, calories, protein, fat, carbs, source, default_unit, popularity_score)
                        VALUES (:id, :name, :category, :calories, :protein, :fat, :carbs, :source, :default_unit, :popularity_score)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": str(food_id),
                        "name": name,
                        "category": category_pl,
                        "calories": p.get("kcal_100g", 0),
                        "protein": p.get("protein_100g", 0),
                        "fat": p.get("fat_100g", 0),
                        "carbs": p.get("carbs_100g", 0),
                        "source": "kunachowicz",
                        "default_unit": "gram",
                        "popularity_score": 15,
                    },
                )

            for idx, u in enumerate(p.get("units", [])):
                u_name = u.get("name")
                u_weight = u.get("weight_g", 0)

                if u_name in UNIT_MAP:
                    u_type, u_label = UNIT_MAP[u_name]
                else:
                    u_type, u_label = guess_unit_type(u_name)

                unit_id = uuid4()

                await session.execute(
                    text("""
                        INSERT INTO food_units (id, food_id, unit, grams, label, priority)
                        VALUES (:id, :food_id, :unit, :grams, :label, :priority)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": str(unit_id),
                        "food_id": str(food_id),
                        "unit": u_type,
                        "grams": u_weight,
                        "label": u_label,
                        "priority": idx,
                    },
                )
                units_counter += 1

            counter += 1
            if counter % 50 == 0:
                logger.info(f"Processed {counter} products...")

        await session.commit()
        logger.info(
            f"Seeding completed: {counter} foods inserted, "
            f"{replaced} openfoodfacts replaced, "
            f"{skipped} duplicates skipped, {units_counter} units inserted."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_polish())
