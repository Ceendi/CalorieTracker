"""add pg_trgm trigram matching to hybrid search

Revision ID: i7j8k9l0m1n2
Revises: h6i7j8k9l0m1
Create Date: 2026-02-18 14:00:00.000000

Replaces simple FTS (plainto_tsquery 'simple') with pg_trgm word_similarity
in the hybrid_food_search function.

Problem with 'simple' FTS:
- Exact token matching only — 'kurczak' does NOT match 'kurczaka'
- Polish morphology has heavy inflection, so FTS recall was poor

pg_trgm word_similarity benefits:
- Handles Polish declension: 'kurczak' <-> 'kurczaka' = 0.88
- Handles plural forms: 'mleko' <-> 'mleka' = 0.67
- Threshold 0.4 filters unrelated words: 'kurczak' <-> 'Kotlet schabowy' = 0.13

Threshold selection (verified empirically):
  - masło / masełko:          0.50  (worst-case inflection, still passes)
  - mleko / mleka:            0.67
  - ryż / ryżu:               0.75
  - ser / sery:               0.75
  - orzechy włoskie / Kotlet orzechowy: 0.38  (false positive, correctly filtered)
  - kurczak / Kotlet schabowy:          0.13  (filtered)
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'i7j8k9l0m1n2'
down_revision: Union[str, Sequence[str], None] = 'h6i7j8k9l0m1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TRGM_THRESHOLD = 0.4


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # GIN index on name for fast trigram lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS foods_name_trgm_idx
        ON foods USING gin (name gin_trgm_ops)
        WHERE source IN ('fineli', 'kunachowicz')
    """)

    op.execute(f"""
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
            SET LOCAL hnsw.ef_search = 200;
            vector_pool := GREATEST(match_limit * 5, 100);

            -- Check if trigram search returns any results above threshold
            SELECT COUNT(*) INTO text_result_count
            FROM foods f
            WHERE word_similarity(query_text, f.name) > {TRGM_THRESHOLD}
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
                    LIMIT vector_pool
                ),
                text_search AS (
                    SELECT
                        f.id,
                        word_similarity(query_text, f.name) AS text_score,
                        ROW_NUMBER() OVER (
                            ORDER BY word_similarity(query_text, f.name) DESC
                        ) AS text_rank
                    FROM foods f
                    WHERE word_similarity(query_text, f.name) > {TRGM_THRESHOLD}
                      AND f.source IN ('fineli', 'kunachowicz')
                    LIMIT vector_pool
                ),
                rrf_scores AS (
                    SELECT
                        COALESCE(v.id, t.id) AS id,
                        COALESCE(1.0 / (60 + v.vector_rank), 0) * vector_weight +
                        COALESCE(1.0 / (60 + t.text_rank),   0) * (1 - vector_weight)
                            AS rrf_score
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
                -- Fallback: vector-only when no trigram matches
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
    op.execute("DROP INDEX IF EXISTS foods_name_trgm_idx")

    # Restore previous version (simple FTS from h6i7j8k9l0m1)
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
            SET LOCAL hnsw.ef_search = 200;
            vector_pool := GREATEST(match_limit * 5, 100);

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
                    LIMIT vector_pool
                ),
                text_search AS (
                    SELECT
                        f.id,
                        ts_rank(f.search_text, plainto_tsquery('simple', query_text)) AS text_score,
                        ROW_NUMBER() OVER (ORDER BY ts_rank(f.search_text, plainto_tsquery('simple', query_text)) DESC) AS text_rank
                    FROM foods f
                    WHERE f.search_text @@ plainto_tsquery('simple', query_text)
                      AND f.source IN ('fineli', 'kunachowicz')
                    LIMIT vector_pool
                ),
                rrf_scores AS (
                    SELECT
                        COALESCE(v.id, t.id) AS id,
                        COALESCE(1.0 / (60 + v.vector_rank), 0) * vector_weight +
                        COALESCE(1.0 / (60 + t.text_rank),   0) * (1 - vector_weight) AS rrf_score
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
