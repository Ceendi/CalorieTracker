"""
Assign Glycemic Index to Foods
===============================
Batch-updates the glycemic_index column in the foods table using keyword
matching against a scientifically-sourced GI reference table.

Conservative strategy: only assigns a value when the match is unambiguous.
Products with ≤ 5 g carbs/100g (meats, fish, fats) are always skipped.
Run this script after the Alembic migration j8k9l0m1n2o3 has been applied.

Usage:
    uv run python scripts/assign_gi.py
    uv run python scripts/assign_gi.py --dry-run   # preview without committing
    uv run python scripts/assign_gi.py --batch-size 500
"""

import asyncio
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.food_catalogue.infrastructure.orm_models import FoodModel
from src.food_catalogue.application.gi_utils import match_gi

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


async def main(batch_size: int = 500, dry_run: bool = False) -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Fetch all foods (id, name, carbs)
        stmt = select(FoodModel.id, FoodModel.name, FoodModel.carbs)
        result = await session.execute(stmt)
        rows = result.all()

    total = len(rows)
    matched = 0
    skipped_low_carb = 0
    no_match = 0

    updates: list[dict] = []

    for row in rows:
        food_id, name, carbs = row.id, row.name, row.carbs
        gi = match_gi(name, carbs)

        if gi is not None:
            matched += 1
            updates.append({"food_id": food_id, "gi": gi})
        elif carbs <= 5.0:
            skipped_low_carb += 1
        else:
            no_match += 1

    logger.info(f"Total foods: {total}")
    logger.info(f"  GI matched:       {matched} ({matched/total*100:.1f}%)")
    logger.info(f"  Low-carb (≤5g):   {skipped_low_carb}")
    logger.info(f"  No match:         {no_match}")

    if dry_run:
        logger.info("Dry run – no database changes made.")
        await engine.dispose()
        return

    # Apply updates in batches
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        committed = 0
        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]
            for item in batch:
                await session.execute(
                    update(FoodModel)
                    .where(FoodModel.id == item["food_id"])
                    .values(glycemic_index=item["gi"])
                )
            await session.commit()
            committed += len(batch)
            logger.info(f"  Committed {committed}/{matched} updates…")

    logger.info("Done.")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assign GI values to foods in DB")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()
    asyncio.run(main(batch_size=args.batch_size, dry_run=args.dry_run))
