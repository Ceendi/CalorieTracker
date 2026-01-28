"""
Embedding service for generating vector embeddings using multilingual-e5-small.

This service provides a lightweight embedding model (384 dimensions) for use with
pgvector hybrid search. The model is loaded once and cached for reuse.
"""

import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger


class EmbeddingService:
    """
    Service for generating text embeddings using multilingual-e5-small model.

    The model produces 384-dimensional embeddings optimized for Polish and
    other European languages. It's ~130MB in size vs 2.2GB for e5-large.
    """

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls, model_name: str = "intfloat/multilingual-e5-small"):
        """Singleton pattern to ensure model is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        if self._initialized:
            return

        self._model_name = model_name
        self._load_model()
        self._initialized = True

    def _load_model(self) -> None:
        """Load the embedding model."""
        if self._model is not None:
            return

        logger.info(f"Loading embedding model: {self._model_name}")
        try:
            EmbeddingService._model = SentenceTransformer(
                self._model_name,
                device="cpu"  # Keep on CPU to leave GPU for Bielik
            )
            logger.info(f"Embedding model loaded successfully (dim={self.embedding_dim})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Embedding model loading failed: {e}")

    @property
    def embedding_dim(self) -> int:
        """Return the embedding dimension (384 for e5-small)."""
        return self._model.get_sentence_embedding_dimension()

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a search query into an embedding vector.

        Args:
            query: The search query text (e.g., "maslo", "mleko 3.2%")

        Returns:
            numpy array of shape (384,) with normalized embedding

        Note:
            Uses "query: " prefix as required by E5 models for asymmetric search.
        """
        prefixed_query = f"query: {query}"
        embedding = self._model.encode(
            prefixed_query,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding

    def encode_passage(self, text: str) -> np.ndarray:
        """
        Encode a passage/document for indexing.

        Args:
            text: The passage text (e.g., product name)

        Returns:
            numpy array of shape (384,) with normalized embedding

        Note:
            Uses "passage: " prefix as required by E5 models for asymmetric search.
        """
        prefixed_text = f"passage: {text}"
        embedding = self._model.encode(
            prefixed_text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding

    def encode_passages_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Encode multiple passages in batch for efficient indexing.

        Args:
            texts: List of passage texts
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            numpy array of shape (n_texts, 384) with normalized embeddings
        """
        prefixed_texts = [f"passage: {t}" for t in texts]
        embeddings = self._model.encode(
            prefixed_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress
        )
        return embeddings

    def is_available(self) -> bool:
        """Check if the model is loaded and available."""
        return self._model is not None

    # Aliases for backward compatibility with task requirements
    def encode(self, text: str) -> np.ndarray:
        """Alias for encode_passage."""
        return self.encode_passage(text)

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Alias for encode_passages_batch."""
        return self.encode_passages_batch(texts, batch_size=batch_size, show_progress=True)

    async def generate_embeddings_for_all_foods(
        self,
        session: AsyncSession,
        batch_size: int = 100
    ) -> int:
        """Generate embeddings for all foods without embedding.

        Args:
            session: Async database session
            batch_size: Number of foods to process per batch

        Returns:
            Number of foods updated with embeddings
        """
        # Get foods without embeddings
        result = await session.execute(text("""
            SELECT id, name FROM foods WHERE embedding IS NULL
        """))
        foods = result.fetchall()

        if not foods:
            logger.info("All foods already have embeddings")
            return 0

        logger.info(f"Generating embeddings for {len(foods)} foods...")

        # Process in batches
        total_updated = 0
        for i in range(0, len(foods), batch_size):
            batch = foods[i:i + batch_size]
            names = [f[1] for f in batch]  # name is at index 1
            ids = [f[0] for f in batch]    # id is at index 0

            # Generate embeddings
            embeddings = self.encode_passages_batch(names, batch_size=32, show_progress=True)

            # Update database
            for food_id, embedding in zip(ids, embeddings):
                embedding_list = embedding.tolist()
                # Format embedding as PostgreSQL vector literal
                vector_str = f"[{','.join(map(str, embedding_list))}]"
                await session.execute(
                    text("UPDATE foods SET embedding = :embedding WHERE id = :id"),
                    {"embedding": vector_str, "id": food_id}
                )

            await session.commit()
            total_updated += len(batch)
            logger.info(f"Progress: {total_updated}/{len(foods)}")

        logger.info(f"Generated embeddings for {total_updated} foods")
        return total_updated

    async def generate_embedding_for_food(
        self,
        session: AsyncSession,
        food_id: str,
        name: str
    ) -> None:
        """Generate and store embedding for a single food.

        Args:
            session: Async database session
            food_id: ID of the food to update
            name: Name of the food to encode
        """
        embedding = self.encode_passage(name)
        embedding_list = embedding.tolist()
        vector_str = f"[{','.join(map(str, embedding_list))}]"

        await session.execute(
            text("UPDATE foods SET embedding = :embedding WHERE id = :id"),
            {"embedding": vector_str, "id": food_id}
        )
        await session.commit()
        logger.debug(f"Generated embedding for food: {name}")


# Singleton accessor function
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton EmbeddingService instance.

    Returns:
        The shared EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
