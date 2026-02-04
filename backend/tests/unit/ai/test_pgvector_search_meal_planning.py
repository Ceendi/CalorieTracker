"""
Unit tests for PgVectorSearchService.search_for_meal_planning query building.

Verifies that:
- meal_description is correctly incorporated into search queries
- embedding query is focused (description + meal type word) for better semantic matching
- FTS query remains broad (description + full base query) for keyword coverage
- diet-based keyword filtering operates on both queries
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from src.ai.infrastructure.search.pgvector_search import PgVectorSearchService


@pytest.fixture
def mock_embedding_service():
    service = MagicMock()
    service.encode_query = MagicMock(return_value=np.zeros(384))
    return service


@pytest.fixture
def mock_session():
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.fixture
def search_service(mock_embedding_service):
    return PgVectorSearchService(embedding_service=mock_embedding_service)


def _get_fts_query(mock_session) -> str:
    """Extract the FTS query string passed to hybrid_food_search."""
    call_kwargs = mock_session.execute.call_args
    return call_kwargs[0][1]["query"]  # positional arg [1] is the params dict


def _get_vector_weight(mock_session) -> float:
    """Extract the vector weight passed to hybrid_food_search."""
    call_kwargs = mock_session.execute.call_args
    return call_kwargs[0][1]["weight"]


class TestMealPlanningQueryBuilding:
    """Tests for query construction in search_for_meal_planning."""

    @pytest.mark.asyncio
    async def test_no_description_embedding_uses_full_base_query(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session, meal_type="breakfast"
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q.startswith("sniadanie platki owsiane")

    @pytest.mark.asyncio
    async def test_no_description_fts_uses_full_base_query(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session, meal_type="breakfast"
        )

        fts_q = _get_fts_query(mock_session)
        assert fts_q.startswith("sniadanie platki owsiane")

    @pytest.mark.asyncio
    async def test_with_description_embedding_is_focused(
        self, search_service, mock_embedding_service, mock_session
    ):
        """Embedding query should be description + meal type word only."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z bananem i migdalami",
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q == "Owsianka z bananem i migdalami sniadanie"

    @pytest.mark.asyncio
    async def test_with_description_fts_is_focused(
        self, search_service, mock_embedding_service, mock_session
    ):
        """FTS query should use only the description — no generic base keywords."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z bananem i migdalami",
        )

        fts_q = _get_fts_query(mock_session)
        assert fts_q == "Owsianka z bananem i migdalami"
        assert "platki owsiane" not in fts_q
        assert "jajka" not in fts_q

    @pytest.mark.asyncio
    async def test_empty_string_description_treated_as_no_description(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session, meal_type="lunch", meal_description=""
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q.startswith("obiad mieso kurczak")

    @pytest.mark.asyncio
    async def test_unknown_meal_type_uses_meal_type_as_query(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session, meal_type="brunch"
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q == "brunch"

    @pytest.mark.asyncio
    async def test_unknown_meal_type_with_description(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="brunch",
            meal_description="Jajka po benedyktynsku",
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q == "Jajka po benedyktynsku brunch"

    @pytest.mark.asyncio
    async def test_lunch_description_embedding_uses_obiad(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="lunch",
            meal_description="Kurczak z ryzem",
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert embedding_q == "Kurczak z ryzem obiad"

    @pytest.mark.asyncio
    async def test_vector_weight_increased_with_description(
        self, search_service, mock_embedding_service, mock_session
    ):
        """When description provided, vector weight should be > 0.5."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
            meal_description="Zupa krem z dyni",
        )

        weight = _get_vector_weight(mock_session)
        assert weight > 0.5

    @pytest.mark.asyncio
    async def test_no_description_keeps_balanced_weight(
        self, search_service, mock_embedding_service, mock_session
    ):
        """Without description, vector weight should be 0.5."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
        )

        weight = _get_vector_weight(mock_session)
        assert weight == 0.5

    @pytest.mark.asyncio
    async def test_no_description_fts_uses_full_base_query_keywords(
        self, search_service, mock_embedding_service, mock_session
    ):
        """Without description, FTS should use full base query with all keywords."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
        )

        fts_q = _get_fts_query(mock_session)
        assert "orzechy" in fts_q
        assert "baton" in fts_q
        assert "jogurt" in fts_q


class TestDietFilteringWithDescription:
    """Tests for diet-based keyword removal on both embedding and FTS queries."""

    @pytest.mark.asyncio
    async def test_keto_removes_carb_keywords_from_embedding(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z bananem",
            preferences={"diet": "keto"},
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert "banan" not in embedding_q
        assert "awokado" in embedding_q
        assert "oliwa" in embedding_q

    @pytest.mark.asyncio
    async def test_keto_removes_carb_keywords_from_fts(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z bananem",
            preferences={"diet": "keto"},
        )

        fts_q = _get_fts_query(mock_session)
        assert "banan" not in fts_q
        assert "platki" not in fts_q
        assert "awokado" in fts_q
        assert "boczek" in fts_q

    @pytest.mark.asyncio
    async def test_keto_embedding_stays_focused(
        self, search_service, mock_embedding_service, mock_session
    ):
        """Keto embedding should not have all the generic keto FTS keywords."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Jajecznica",
            preferences={"diet": "keto"},
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        # Focused: description + meal_type_word + keto essentials
        assert "Jajecznica" in embedding_q
        assert "sniadanie" in embedding_q
        # Should NOT have all the FTS-only keto keywords
        assert "boczek" not in embedding_q
        assert "ryby" not in embedding_q

    @pytest.mark.asyncio
    async def test_vegan_removes_animal_keywords_from_embedding(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z mlekiem",
            preferences={"diet": "vegan"},
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert "mleko" not in embedding_q.split()
        assert "tofu" in embedding_q
        assert "soczewica" in embedding_q

    @pytest.mark.asyncio
    async def test_vegan_fts_has_full_plant_keywords(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka",
            preferences={"diet": "vegan"},
        )

        fts_q = _get_fts_query(mock_session)
        assert "tofu" in fts_q
        assert "ciecierzyca" in fts_q
        assert "mleko_roslinne" in fts_q
        assert "hummus" in fts_q

    @pytest.mark.asyncio
    async def test_keto_removes_chleb_from_description(
        self, search_service, mock_embedding_service, mock_session
    ):
        """If description contains a keto-excluded keyword, it gets removed."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="dinner",
            meal_description="Kanapka z chleb razowy",
            preferences={"diet": "keto"},
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert "chleb" not in embedding_q

        fts_q = _get_fts_query(mock_session)
        assert "chleb" not in fts_q

    @pytest.mark.asyncio
    async def test_no_diet_preserves_full_queries(
        self, search_service, mock_embedding_service, mock_session
    ):
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="breakfast",
            meal_description="Owsianka z bananem",
            preferences={"diet": None},
        )

        embedding_q = mock_embedding_service.encode_query.call_args[0][0]
        assert "Owsianka z bananem" in embedding_q
        assert "sniadanie" in embedding_q

        fts_q = _get_fts_query(mock_session)
        assert "Owsianka z bananem" in fts_q
        # With description provided, FTS is focused — no base keywords appended
        assert "platki owsiane" not in fts_q
