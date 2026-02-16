"""add kunachowicz source to hybrid search and index

Revision ID: g5h6i7j8k9l0
Revises: f4a5b6c7d8e9
Create Date: 2026-02-16 20:00:00.000000

Updates hybrid_food_search function and partial HNSW index to include
products from the 'kunachowicz' source alongside 'fineli'.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'g5h6i7j8k9l0'
down_revision: Union[str, Sequence[str], None] = 'f4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update hybrid_food_search and HNSW index to include kunachowicz source."""

    # Recreate partial HNSW index to include both sources
    op.execute("DROP INDEX IF EXISTS foods_embedding_fineli_hnsw_idx")
    op.execute("""
        CREATE INDEX foods_embedding_verified_hnsw_idx
        ON foods USING hnsw (embedding vector_cosine_ops)
        WITH (m = 24, ef_construction = 128)
        WHERE source IN ('fineli', 'kunachowicz') AND embedding IS NOT NULL
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
              AND f.source IN ('fineli', 'kunachowicz');

            IF text_result_count > 0 THEN
                -- Use hybrid search (vector + FTS with RRF)
                RETURN QUERY
                WITH vector_search AS (
                    SELECT
                        f.id,
                        1 - (f.embedding <=> query_embedding) AS vector_score,
                        ROW_NUMBER() OVER (ORDER BY f.embedding <=> query_embedding) AS vector_rank
                    FROM foods f
                    WHERE f.embedding IS NOT NULL AND f.source IN ('fineli', 'kunachowicz')
                    ORDER BY f.embedding <=> query_embedding
                    LIMIT match_limit * 2
                ),
                text_search AS (
                    SELECT
                        f.id,
                        ts_rank(f.search_text, plainto_tsquery('simple', query_text)) AS text_score,
                        ROW_NUMBER() OVER (ORDER BY ts_rank(f.search_text, plainto_tsquery('simple', query_text)) DESC) AS text_rank
                    FROM foods f
                    WHERE f.search_text @@ plainto_tsquery('simple', query_text) AND f.source IN ('fineli', 'kunachowicz')
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
                WHERE f.embedding IS NOT NULL AND f.source IN ('fineli', 'kunachowicz')
                ORDER BY f.embedding <=> query_embedding
                LIMIT match_limit;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to fineli-only source filter."""
    op.execute("DROP INDEX IF EXISTS foods_embedding_verified_hnsw_idx")
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
            SELECT COUNT(*) INTO text_result_count
            FROM foods f
            WHERE f.search_text @@ plainto_tsquery('simple', query_text)
              AND f.source = 'fineli';

            IF text_result_count > 0 THEN
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
