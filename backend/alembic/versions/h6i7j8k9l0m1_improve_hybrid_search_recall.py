"""improve hybrid search recall with larger candidate pool and ef_search tuning

Revision ID: h6i7j8k9l0m1
Revises: g5h6i7j8k9l0
Create Date: 2026-02-18 12:00:00.000000

Fixes the issue where relevant products (e.g. "Orzechy włoskie") could be
missing from hybrid search results when the vector candidate pool was too small.

Changes:
1. Increases vector_search CTE limit from match_limit * 2 to GREATEST(match_limit * 5, 100)
   — ensures at least 100 candidates are considered for RRF, preventing near-misses
2. Sets hnsw.ef_search = 200 within the function for better HNSW approximate recall
   — without this, the HNSW graph may skip relevant nodes during beam search
3. Increases text_search CTE limit from match_limit * 2 to match_limit * 5
   — consistent with vector_search pool size

Root cause analysis:
- HNSW default ef_search = 40 means the beam only explores 40 nodes
- vector_search LIMIT = match_limit * 2 = 40 for typical match_limit=20
- With 2000+ products and tight HNSW beam, semantically close products
  (e.g. "Orzechy włoskie" among many nut-related products) could fall
  outside the candidate window, preventing them from appearing in results
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'h6i7j8k9l0m1'
down_revision: Union[str, Sequence[str], None] = 'g5h6i7j8k9l0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase vector candidate pool and HNSW ef_search for better recall."""

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
            vector_pool INT;
        BEGIN
            -- Expand HNSW beam to explore more graph nodes for better recall.
            -- Default ef_search = 40 is too tight when the DB has 2000+ products.
            SET LOCAL hnsw.ef_search = 200;

            -- Use at least 100 candidates for RRF, even for small match_limit values.
            vector_pool := GREATEST(match_limit * 5, 100);

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
                    LIMIT vector_pool
                ),
                text_search AS (
                    SELECT
                        f.id,
                        ts_rank(f.search_text, plainto_tsquery('simple', query_text)) AS text_score,
                        ROW_NUMBER() OVER (ORDER BY ts_rank(f.search_text, plainto_tsquery('simple', query_text)) DESC) AS text_rank
                    FROM foods f
                    WHERE f.search_text @@ plainto_tsquery('simple', query_text) AND f.source IN ('fineli', 'kunachowicz')
                    LIMIT vector_pool
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
    """Revert to previous version with smaller candidate pool."""

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
              AND f.source IN ('fineli', 'kunachowicz');

            IF text_result_count > 0 THEN
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
