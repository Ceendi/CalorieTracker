"""fix hybrid search source filter and add vector-only fallback

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-01-29 10:00:00.000000

This migration fixes the hybrid_food_search function by:
1. Adding 'source = fineli' filter to only search products with nutritional data
2. Adding fallback to vector-only search when FTS returns 0 results
3. Creating a partial HNSW index for fineli products to improve vector search recall

Without this fix, hybrid search may return 0 products when text queries
don't match (e.g., Polish queries with English product names), causing
meal planning to fail with "Invalid product index" errors.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, Sequence[str], None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update hybrid_food_search function with source filter and vector-only fallback."""

    # Create partial HNSW index for fineli products only
    # This improves vector search recall when filtering by source='fineli'
    # Without this, HNSW may skip relevant results after post-filtering
    op.execute("DROP INDEX IF EXISTS foods_embedding_fineli_hnsw_idx")
    op.execute("""
        CREATE INDEX foods_embedding_fineli_hnsw_idx
        ON foods USING hnsw (embedding vector_cosine_ops)
        WITH (m = 24, ef_construction = 128)
        WHERE source = 'fineli' AND embedding IS NOT NULL
    """)

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
        DECLARE
            text_result_count INT;
        BEGIN
            -- Check if FTS returns any results
            SELECT COUNT(*) INTO text_result_count
            FROM foods f
            WHERE f.search_text @@ plainto_tsquery('simple', query_text)
              AND f.source = 'fineli';

            IF text_result_count > 0 THEN
                -- Use hybrid search (vector + FTS with RRF)
                RETURN QUERY
                WITH vector_search AS (
                    SELECT
                        f.id,
                        1 - (f.embedding <=> query_embedding) AS vector_score,
                        ROW_NUMBER() OVER (ORDER BY f.embedding <=> query_embedding) AS vector_rank
                    FROM foods f
                    WHERE f.embedding IS NOT NULL AND f.source = 'fineli'
                    ORDER BY f.embedding <=> query_embedding
                    LIMIT match_limit * 2
                ),
                text_search AS (
                    SELECT
                        f.id,
                        ts_rank(f.search_text, plainto_tsquery('simple', query_text)) AS text_score,
                        ROW_NUMBER() OVER (ORDER BY ts_rank(f.search_text, plainto_tsquery('simple', query_text)) DESC) AS text_rank
                    FROM foods f
                    WHERE f.search_text @@ plainto_tsquery('simple', query_text) AND f.source = 'fineli'
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
                    f.name::text,
                    f.category::text,
                    f.calories,
                    f.protein,
                    f.fat,
                    f.carbs,
                    r.rrf_score AS score
                FROM rrf_scores r
                JOIN foods f ON f.id = r.id
                ORDER BY r.rrf_score DESC
                LIMIT match_limit;
            ELSE
                -- Fallback: vector-only search when FTS returns nothing
                RETURN QUERY
                SELECT
                    f.id,
                    f.name::text,
                    f.category::text,
                    f.calories,
                    f.protein,
                    f.fat,
                    f.carbs,
                    (1 - (f.embedding <=> query_embedding))::float AS score
                FROM foods f
                WHERE f.embedding IS NOT NULL AND f.source = 'fineli'
                ORDER BY f.embedding <=> query_embedding
                LIMIT match_limit;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to original hybrid_food_search without source filter."""
    # Drop partial index
    op.execute("DROP INDEX IF EXISTS foods_embedding_fineli_hnsw_idx")

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
