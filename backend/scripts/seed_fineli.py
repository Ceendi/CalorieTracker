"""
Seed Fineli Products to Database
================================
Seeds the fineli_products.json into the foods and food_units tables.
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

DATA_PATH = Path(__file__).parent.parent / "seeds" / "fineli_products.json"

CATEGORY_MAP = {
    "VEGFRESH": "Warzywa", "VEGCANN": "Warzywa", "VEGPOT": "Warzywa",
    "VEGDISH": "Dania wegetariańskie", "VEGJUICE": "Napoje roślinne",
    "FRUFRESH": "Owoce", "BERFRESH": "Owoce", "FRUBDISH": "Owoce", "FRUBJUIC": "Soki",
    "MEATCUTS": "Mięso", "MSTEAK": "Mięso", "POULTRY": "Drób",
    "SAUSAGE": "Mięso", "SAUSCUTS": "Wędliny", "MEATPROD": "Mięso",
    "FISH": "Ryby", "SEAFOOD": "Owoce morza", "FISHPROD": "Ryby",
    "MILKFF": "Nabiał", "MILKHF": "Nabiał", "MILKLF": "Nabiał",
    "SMILK": "Nabiał", "CREAM": "Nabiał", "SOUCREAM": "Nabiał",
    "YOGHURT": "Nabiał", "CURD": "Nabiał",
    "CHEESUNC": "Sery", "CHEESPRO": "Sery", "CHEESCUR": "Sery",
    "BUTTER": "Tłuszcze", "BUTTEHIG": "Tłuszcze", "BUTTELOW": "Tłuszcze",
    "EGGS": "Nabiał", "EGGMIX": "Dania z jaj",
    "FLOUR": "Produkty zbożowe", "PORR": "Produkty zbożowe",
    "CERBAR": "Produkty zbożowe", "CERBRKF": "Płatki śniadaniowe",
    "LEGUMES": "Warzywa", "LEGUPROD": "Produkty wegańskie",
    "OIL": "Tłuszcze", "FATCOOK": "Tłuszcze", "FATANIM": "Tłuszcze",
    "VEGFATHI": "Tłuszcze", "VEGFATLO": "Tłuszcze",
    "SUGADD": "Cukier i słodziki", "INGRMISC": "Inne",
    "SPICES": "Przyprawy", "SAVSAUCE": "Sosy", "SPISAUCE": "Sosy",
    "BRWHITE": "Pieczywo", "BRRYE": "Pieczywo", "BRMIX": "Pieczywo", "BUN": "Pieczywo",
}

UNIT_MAP = {
    "Sztuka": ("piece", "sztuka"),
    "Sztuka (mała)": ("piece", "sztuka"),
    "Sztuka (średnia)": ("piece", "sztuka"),
    "Sztuka (duża)": ("piece", "sztuka"),
    "Łyżka": ("tablespoon", "łyżka"),
    "Łyżeczka": ("teaspoon", "łyżeczka"),
    "Szklanka": ("cup", "szklanka"),
    "Porcja": ("portion", "porcja"),
    "Porcja (mała)": ("portion", "porcja"),
    "Porcja (średnia)": ("portion", "porcja"),
    "Porcja (duża)": ("portion", "porcja"),
}


async def seed_fineli():
    logger.info("Starting Fineli seeding...")

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
        units_counter = 0

        for p in products:
            food_id = uuid4()

            name = p.get("name_pl") or p.get("name_en", "Unknown")

            cat_code = p.get("category", "INGRMISC")
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
                    "source": "fineli",
                    "default_unit": "gram",
                    "popularity_score": 10,
                }
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
                        }
                    )
                    units_counter += 1
            
            counter += 1
            if counter % 200 == 0:
                logger.info(f"Processed {counter} products...")
        
        await session.commit()
        logger.info(f"Seeding completed: {counter} foods, {units_counter} units inserted.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_fineli())
