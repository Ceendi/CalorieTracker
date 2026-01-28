"""add pgvector hybrid search

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgvector extension, embedding column, search_text tsvector, and hybrid search function."""

    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Add embedding column (384 dimensions for E5-small)
    # Using raw SQL because SQLAlchemy doesn't have native vector type
    op.execute("ALTER TABLE foods ADD COLUMN IF NOT EXISTS embedding vector(384)")

    # 3. Add search_text tsvector column (generated from name)
    op.execute("""
        ALTER TABLE foods
        ADD COLUMN IF NOT EXISTS search_text tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', coalesce(name, ''))) STORED
    """)

    # 4. Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS foods_embedding_hnsw_idx
        ON foods USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # 5. Create GIN index for full-text search
    op.execute("""
        CREATE INDEX IF NOT EXISTS foods_search_text_gin_idx
        ON foods USING GIN (search_text)
    """)

    # 6. Create hybrid_food_search function using Reciprocal Rank Fusion (RRF)
    op.execute("""
        CREATE OR REPLACE FUNCTION hybrid_food_search(
            query_text TEXT,
            query_embedding vector(384),
            match_limit INT DEFAULT 20,
            vector_weight FLOAT DEFAULT 0.5
        )
        RETURNS TABLE (
            id UUID,
            name TEXT,
            category TEXT,
            calories FLOAT,
            protein FLOAT,
            fat FLOAT,
            carbs FLOAT,
            score FLOAT
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH vector_search AS (
                SELECT
                    f.id,
                    1 - (f.embedding <=> query_embedding) AS vector_score,
                    ROW_NUMBER() OVER (ORDER BY f.embedding <=> query_embedding) AS vector_rank
                FROM foods f
                WHERE f.embedding IS NOT NULL
                ORDER BY f.embedding <=> query_embedding
                LIMIT match_limit * 2
            ),
            text_search AS (
                SELECT
                    f.id,
                    ts_rank(f.search_text, plainto_tsquery('simple', query_text)) AS text_score,
                    ROW_NUMBER() OVER (ORDER BY ts_rank(f.search_text, plainto_tsquery('simple', query_text)) DESC) AS text_rank
                FROM foods f
                WHERE f.search_text @@ plainto_tsquery('simple', query_text)
                LIMIT match_limit * 2
            ),
            rrf_scores AS (
                SELECT
                    COALESCE(v.id, t.id) AS id,
                    COALESCE(1.0 / (60 + v.vector_rank), 0) * vector_weight +
                    COALESCE(1.0 / (60 + t.text_rank), 0) * (1 - vector_weight) AS rrf_score
                FROM vector_search v
                FULL OUTER JOIN text_search t ON v.id = t.id
            )
            SELECT
                f.id,
                f.name,
                f.category,
                f.calories,
                f.protein,
                f.fat,
                f.carbs,
                r.rrf_score AS score
            FROM rrf_scores r
            JOIN foods f ON f.id = r.id
            ORDER BY r.rrf_score DESC
            LIMIT match_limit;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Remove hybrid search function, indexes, and columns."""

    # Drop the hybrid search function
    op.execute("DROP FUNCTION IF EXISTS hybrid_food_search(TEXT, vector(384), INT, FLOAT)")

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS foods_search_text_gin_idx")
    op.execute("DROP INDEX IF EXISTS foods_embedding_hnsw_idx")

    # Drop columns
    op.execute("ALTER TABLE foods DROP COLUMN IF EXISTS search_text")
    op.execute("ALTER TABLE foods DROP COLUMN IF EXISTS embedding")

    # Note: We don't drop the pgvector extension as other tables might use it
