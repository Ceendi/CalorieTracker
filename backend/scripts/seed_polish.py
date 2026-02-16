"""
Seed Polish Products to Database
=================================
Seeds the polish_products.json into the foods and food_units tables.
Adds ~107 Polish food products missing from the Fineli database.

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
    # New categories for Polish products
    "POTATO": "Ziemniaki i skrobie",
    "RICE": "Produkty zbożowe",
    "PASTA": "Produkty zbożowe",
    "BREAD": "Pieczywo",
    "GRAIN": "Produkty zbożowe",
    "NUTS": "Orzechy i nasiona",
    "SEEDS": "Orzechy i nasiona",
    "DRIED_FRUIT": "Owoce suszone",
    "MUSHROOM": "Grzyby",
    "SWEETS": "Słodycze",
    "SNACKS": "Przekąski",
    "BEVERAGE": "Napoje",
    "DAIRY": "Nabiał",
    "DELI": "Wędliny",
    "CONDIMENT": "Sosy i dodatki",
    "ICE_CREAM": "Lody",
    "POLISH_DISH": "Dania polskie",
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
        units_counter = 0

        for p in products:
            name = p.get("name_pl") or p.get("name_en", "Unknown")

            # Check for duplicate by name
            result = await session.execute(
                text("SELECT id FROM foods WHERE name = :name"),
                {"name": name},
            )
            existing = result.fetchone()
            if existing:
                logger.debug(f"Skipping duplicate: {name}")
                skipped += 1
                continue

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
            f"{skipped} duplicates skipped, {units_counter} units inserted."
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_polish())
