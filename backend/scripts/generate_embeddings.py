"""
Generate Embeddings for Foods
=============================
Generates vector embeddings for all foods in the database using
the multilingual-e5-small model (384 dimensions).

Usage:
    python scripts/generate_embeddings.py

    # Or with custom batch size:
    python scripts/generate_embeddings.py --batch-size 50
"""

import asyncio
import sys
import os
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.ai.infrastructure.embedding import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(batch_size: int = 100):
    """Generate embeddings for all foods without embeddings.

    Args:
        batch_size: Number of foods to process per batch
    """
    logger.info("Starting embedding generation...")
    logger.info(f"Batch size: {batch_size}")

    # Initialize embedding service (loads model once)
    service = EmbeddingService()
    logger.info(f"Model loaded: {service._model_name}")
    logger.info(f"Embedding dimension: {service.embedding_dim}")

    # Create database session
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        count = await service.generate_embeddings_for_all_foods(
            session=session,
            batch_size=batch_size
        )
        logger.info(f"Generated {count} embeddings")

    await engine.dispose()
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for foods")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of foods to process per batch (default: 100)"
    )
    args = parser.parse_args()

    asyncio.run(main(batch_size=args.batch_size))
