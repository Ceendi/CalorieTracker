"""
Tests for PgVectorSearchAdapter.

Target: src/ai/infrastructure/search/pgvector_search_adapter.py
Mocks: PgVectorSearchService, AsyncSession
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.ai.domain.models import SearchCandidate
from src.ai.infrastructure.search.pgvector_search_adapter import PgVectorSearchAdapter


def _make_candidate(name="mleko 3.2%", score=0.85, product_id=None):
    return SearchCandidate(
        product_id=product_id or str(uuid.uuid4()),
        name=name,
        score=score,
        category="DAI",
    )


@pytest.fixture
def mock_search_service():
    service = MagicMock()
    service.search = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def adapter(mock_search_service, mock_session):
    return PgVectorSearchAdapter(
        search_service=mock_search_service,
        session=mock_session,
    )


# ============================================================================
# TestSearch
# ============================================================================


class TestSearch:
    @pytest.mark.asyncio
    async def test_delegates_to_service(self, adapter, mock_search_service, mock_session):
        candidates = [_make_candidate()]
        mock_search_service.search.return_value = candidates

        # Mock _fetch_product_data to avoid DB calls
        adapter._fetch_product_data = AsyncMock(return_value={
            "id": candidates[0].product_id,
            "name_pl": "mleko 3.2%",
            "name_en": "",
            "category": "DAI",
            "kcal_100g": 60,
            "protein_100g": 3.2,
            "fat_100g": 3.2,
            "carbs_100g": 4.8,
            "source": "fineli",
            "units": [],
        })

        result = await adapter.search("mleko", top_k=10, alpha=0.5)

        mock_search_service.search.assert_called_once_with(
            session=mock_session,
            query="mleko",
            limit=10,
            vector_weight=0.5,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_alpha_mapped_to_vector_weight(self, adapter, mock_search_service):
        mock_search_service.search.return_value = []
        await adapter.search("test", alpha=0.7)

        call_kwargs = mock_search_service.search.call_args[1]
        assert call_kwargs["vector_weight"] == 0.7

    @pytest.mark.asyncio
    async def test_caches_products(self, adapter, mock_search_service):
        pid = str(uuid.uuid4())
        candidates = [_make_candidate(product_id=pid)]
        mock_search_service.search.return_value = candidates

        product_data = {"id": pid, "name_pl": "mleko", "kcal_100g": 60}
        adapter._fetch_product_data = AsyncMock(return_value=product_data)

        await adapter.search("mleko")
        assert adapter._products_cache[pid] == product_data

    @pytest.mark.asyncio
    async def test_returns_candidates(self, adapter, mock_search_service):
        candidates = [_make_candidate(), _make_candidate(name="kefir")]
        mock_search_service.search.return_value = candidates
        adapter._fetch_product_data = AsyncMock(return_value={"id": "x"})

        result = await adapter.search("mleko")
        assert len(result) == 2


# ============================================================================
# TestGetProductById
# ============================================================================


class TestGetProductById:
    def test_returns_cached(self, adapter):
        pid = str(uuid.uuid4())
        adapter._products_cache[pid] = {"name_pl": "mleko", "kcal_100g": 60}
        result = adapter.get_product_by_id(pid)
        assert result["name_pl"] == "mleko"

    def test_returns_none_for_uncached(self, adapter):
        result = adapter.get_product_by_id(str(uuid.uuid4()))
        assert result is None

    def test_string_conversion(self, adapter):
        pid = uuid.uuid4()
        adapter._products_cache[str(pid)] = {"name_pl": "ser"}
        result = adapter.get_product_by_id(str(pid))
        assert result["name_pl"] == "ser"


# ============================================================================
# TestFetchProductData
# ============================================================================


class TestFetchProductData:
    @pytest.mark.asyncio
    async def test_fetches_food_and_units(self, adapter, mock_session):
        pid = str(uuid.uuid4())

        # Mock the food query
        food_row = MagicMock()
        food_row.id = pid
        food_row.name = "mleko 3.2%"
        food_row.category = "DAI"
        food_row.calories = 60
        food_row.protein = 3.2
        food_row.fat = 3.2
        food_row.carbs = 4.8
        food_row.source = "fineli"

        food_result = MagicMock()
        food_result.fetchone.return_value = food_row

        # Mock the units query
        unit_row = MagicMock()
        unit_row.label = "szklanka"
        unit_row.grams = 250.0

        units_result = MagicMock()
        units_result.fetchall.return_value = [unit_row]

        mock_session.execute.side_effect = [food_result, units_result]

        result = await adapter._fetch_product_data(pid)
        assert result is not None
        assert result["name_pl"] == "mleko 3.2%"
        assert result["kcal_100g"] == 60
        assert len(result["units"]) == 1
        assert result["units"][0]["name"] == "szklanka"
        assert result["units"][0]["weight_g"] == 250.0

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, adapter, mock_session):
        mock_session.execute.side_effect = Exception("DB Error")
        result = await adapter._fetch_product_data("some-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_row(self, adapter, mock_session):
        empty_result = MagicMock()
        empty_result.fetchone.return_value = None
        mock_session.execute.return_value = empty_result

        result = await adapter._fetch_product_data("nonexistent-id")
        assert result is None


# ============================================================================
# TestMiscellaneous
# ============================================================================


class TestMiscellaneous:
    def test_index_products_is_noop(self, adapter):
        # Should not raise
        adapter.index_products([{"name": "test"}])

    def test_products_property_returns_empty(self, adapter):
        assert adapter.products == []

    def test_products_by_id_returns_cache(self, adapter):
        adapter._products_cache["abc"] = {"name": "test"}
        assert adapter.products_by_id == {"abc": {"name": "test"}}

    def test_embeddings_attribute(self, adapter):
        assert adapter.embeddings is True
