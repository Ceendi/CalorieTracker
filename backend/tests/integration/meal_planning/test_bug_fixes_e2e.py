"""
Integration tests for meal planning bug fixes:
- Bug 1: Allergies not respected (jajko → jajecznica passes through)
- Bug 2: Snack repeated 3 times in a day
- Bug 3: Wrong ingredients (baton zbożowy for zupa krem z dyni)
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from src.ai.infrastructure.search.pgvector_search import PgVectorSearchService
from src.meal_planning.adapters.bielik_meal_planner import BielikMealPlannerAdapter
from src.meal_planning.application.service import MealPlanService
from src.meal_planning.domain.entities import PlanPreferences
from tests.unit.meal_planning.conftest import (
    make_ingredient,
    make_meal,
    make_template,
    make_profile,
    make_product,
    make_user_data,
)


class TestAllergenFilteringE2E:
    """E2E tests verifying allergens are blocked at every layer."""

    def test_jajko_allergy_blocks_jajecznica_in_product_filter(self):
        """'jajko' allergy must block 'Jajecznica na masle' via stem matching."""
        service = PgVectorSearchService(embedding_service=None)
        products = [
            {"name": "Jajecznica na masle", "category": "Dania z jaj"},
            {"name": "Kurczak pieczony", "category": "Drob"},
            {"name": "Ryz bialy", "category": "Zboza"},
        ]
        filtered = service._filter_by_preferences(
            products, {"allergies": ["jajko"]}
        )
        names = [p["name"] for p in filtered]
        assert "Jajecznica na masle" not in names, \
            "SAFETY: 'jajko' allergy did NOT block 'Jajecznica na masle'"

    def test_jajko_allergy_blocks_by_category(self):
        """Egg allergy blocks products by category even if name doesn't match stems."""
        service = PgVectorSearchService(embedding_service=None)
        products = [
            {"name": "Produkt X", "category": "Dania z jaj"},
        ]
        filtered = service._filter_by_preferences(
            products, {"allergies": ["jajko"]}
        )
        assert len(filtered) == 0

    def test_gluten_allergy_blocks_bread_products(self):
        """Gluten allergy blocks wheat/bread products."""
        service = PgVectorSearchService(embedding_service=None)
        products = [
            {"name": "Chleb pszenny", "category": "Pieczywo"},
            {"name": "Makaron pszenny", "category": "Produkty zbożowe"},
            {"name": "Ryz bialy", "category": "Zboza"},
        ]
        filtered = service._filter_by_preferences(
            products, {"allergies": ["gluten"]}
        )
        names = [p["name"] for p in filtered]
        assert "Chleb pszenny" not in names
        assert "Makaron pszenny" not in names
        assert "Ryz bialy" in names

    def test_unknown_allergen_falls_back_to_substring(self):
        """Unknown allergens (not in stems map) use simple substring matching."""
        service = PgVectorSearchService(embedding_service=None)
        products = [
            {"name": "Sezamki", "category": "Slodycze"},
            {"name": "Kurczak pieczony", "category": "Drob"},
        ]
        filtered = service._filter_by_preferences(
            products, {"allergies": ["sezam"]}
        )
        names = [p["name"] for p in filtered]
        assert "Sezamki" not in names
        assert "Kurczak pieczony" in names

    def test_template_with_allergen_description_is_replaced(self):
        """Templates containing allergen keywords are replaced with safe defaults."""
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        templates = [[
            make_template(
                meal_type="breakfast",
                description="Jajecznica z pomidorami",
            ),
            make_template(
                meal_type="lunch",
                description="Kurczak z ryzem",
            ),
        ]]
        profile = make_profile(preferences={"allergies": ["jajko"]})

        result = adapter._filter_templates_by_allergies(templates, profile)

        # Jajecznica should be replaced with safe default
        assert result[0][0].description != "Jajecznica z pomidorami"
        assert "jajec" not in result[0][0].description.lower()
        # Kurczak should remain unchanged
        assert result[0][1].description == "Kurczak z ryzem"

    @pytest.mark.asyncio
    async def test_full_pipeline_no_allergens_in_final_plan(self):
        """E2E: with mocked LLM, validate zero allergen violations in plan."""
        mock_repo = AsyncMock()
        mock_planner = AsyncMock()

        # LLM returns templates — one contains egg
        mock_planner.generate_meal_templates = AsyncMock(
            return_value=[[
                make_template("breakfast", description="Sniadanie"),
                make_template("lunch", description="Obiad"),
                make_template("second_breakfast", description="Drugie sniadanie"),
                make_template("snack", description="Podwieczorek"),
                make_template("dinner", description="Kolacja"),
            ]]
        )

        # LLM generates meals with safe ingredients (no eggs)
        safe_meal = make_meal(
            ingredients=[
                make_ingredient(name="Kurczak pieczony"),
                make_ingredient(name="Ryz bialy"),
            ]
        )
        mock_planner.generate_meal = AsyncMock(return_value=safe_meal)
        mock_planner.optimize_plan = AsyncMock(side_effect=lambda days, profile: days)

        mock_food_search = AsyncMock()
        mock_food_search.search_for_meal_planning = AsyncMock(return_value=[])
        mock_food_search.find_product_by_name = AsyncMock(return_value=None)

        service = MealPlanService(
            repository=mock_repo,
            planner=mock_planner,
            food_search=mock_food_search,
            session=MagicMock(),
        )

        user = make_user_data()
        prefs = PlanPreferences(allergies=["jajko"])

        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=1)

        # Validate no allergen violations
        validation = plan.generation_metadata["quality_validation"]
        assert len(validation["allergen_violations"]) == 0, \
            f"Allergen violations found: {validation['allergen_violations']}"


class TestMealTypeDeduplicationE2E:
    """E2E tests verifying no duplicate meal types per day."""

    def test_parse_templates_deduplicates_meal_types(self):
        """3 snacks from LLM → only 1 kept."""
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        # Simulate LLM returning 3 snacks
        import json
        llm_response = json.dumps({
            "days": [{
                "meals": [
                    {"type": "breakfast", "description": "Sniadanie"},
                    {"type": "snack", "description": "Przekaska 1"},
                    {"type": "snack", "description": "Przekaska 2"},
                    {"type": "snack", "description": "Przekaska 3"},
                ]
            }]
        })

        profile = make_profile()
        result = adapter._parse_templates(llm_response, profile, 1)

        # Should have exactly 1 snack (first one kept)
        snack_count = sum(1 for t in result[0] if t.meal_type == "snack")
        assert snack_count == 1, f"Expected 1 snack, got {snack_count}"
        # The kept snack should be the first one
        snack = next(t for t in result[0] if t.meal_type == "snack")
        assert snack.description == "Przekaska 1"

    def test_missing_meal_types_are_filled(self):
        """Missing dinner added as default template."""
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        import json
        llm_response = json.dumps({
            "days": [{
                "meals": [
                    {"type": "breakfast", "description": "Sniadanie"},
                    {"type": "lunch", "description": "Obiad"},
                    # Missing: second_breakfast, snack, dinner
                ]
            }]
        })

        profile = make_profile()
        result = adapter._parse_templates(llm_response, profile, 1)

        types = {t.meal_type for t in result[0]}
        assert "dinner" in types, "Missing dinner was not filled in"
        assert "snack" in types, "Missing snack was not filled in"
        assert "second_breakfast" in types, "Missing second_breakfast was not filled in"

    def test_all_meals_same_type_keeps_only_one(self):
        """5 breakfasts from LLM → 1 breakfast + 4 defaults for other types."""
        adapter = BielikMealPlannerAdapter.__new__(BielikMealPlannerAdapter)
        adapter._model = None
        adapter._embedding_service = None

        import json
        llm_response = json.dumps({
            "days": [{
                "meals": [
                    {"type": "breakfast", "description": f"Sniadanie {i}"}
                    for i in range(5)
                ]
            }]
        })

        profile = make_profile()
        result = adapter._parse_templates(llm_response, profile, 1)

        types = [t.meal_type for t in result[0]]
        breakfast_count = types.count("breakfast")
        assert breakfast_count == 1, f"Expected 1 breakfast, got {breakfast_count}"
        # Should have all 5 expected types
        assert set(types) == {"breakfast", "second_breakfast", "lunch", "snack", "dinner"}

    @pytest.mark.asyncio
    async def test_generate_plan_no_duplicate_meal_types_in_day(self):
        """Full pipeline: no day should have duplicate meal types."""
        mock_repo = AsyncMock()
        mock_planner = AsyncMock()

        # Return templates with duplicates — service should deduplicate
        mock_planner.generate_meal_templates = AsyncMock(
            return_value=[[
                make_template("breakfast"),
                make_template("lunch"),
                make_template("snack"),
                make_template("snack"),  # duplicate!
                make_template("dinner"),
                make_template("second_breakfast"),
            ]]
        )
        mock_planner.generate_meal = AsyncMock(
            side_effect=lambda template, **kwargs: make_meal(meal_type=template.meal_type)
        )
        mock_planner.optimize_plan = AsyncMock(side_effect=lambda days, profile: days)

        mock_food_search = AsyncMock()
        mock_food_search.search_for_meal_planning = AsyncMock(return_value=[])
        mock_food_search.find_product_by_name = AsyncMock(return_value=None)

        service = MealPlanService(
            repository=mock_repo,
            planner=mock_planner,
            food_search=mock_food_search,
            session=MagicMock(),
        )

        user = make_user_data()
        prefs = PlanPreferences()
        plan = await service.generate_plan(user, prefs, date(2026, 1, 1), days=1)

        for day in plan.days:
            meal_types = [m.meal_type for m in day.meals]
            assert len(meal_types) == len(set(meal_types)), \
                f"Day {day.day_number} has duplicate meal types: {meal_types}"


class TestSearchQueryFocusE2E:
    """E2E tests verifying FTS uses only description when available."""

    @pytest.fixture
    def mock_embedding_service(self):
        service = MagicMock()
        service.encode_query = MagicMock(return_value=np.zeros(384))
        return service

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        result = MagicMock()
        result.fetchall.return_value = []
        session.execute = AsyncMock(return_value=result)
        return session

    @pytest.fixture
    def search_service(self, mock_embedding_service):
        return PgVectorSearchService(embedding_service=mock_embedding_service)

    def _get_fts_query(self, mock_session) -> str:
        call_kwargs = mock_session.execute.call_args
        return call_kwargs[0][1]["query"]

    def _get_vector_weight(self, mock_session) -> float:
        call_kwargs = mock_session.execute.call_args
        return call_kwargs[0][1]["weight"]

    @pytest.mark.asyncio
    async def test_description_only_in_fts_query(
        self, search_service, mock_session
    ):
        """FTS query for 'Zupa krem z dyni' should NOT contain 'baton', 'orzechy'."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
            meal_description="Zupa krem z dyni",
        )

        fts_q = self._get_fts_query(mock_session)
        assert "baton" not in fts_q, f"FTS query contains 'baton': {fts_q}"
        assert "orzechy" not in fts_q, f"FTS query contains 'orzechy': {fts_q}"
        assert "Zupa krem z dyni" in fts_q

    @pytest.mark.asyncio
    async def test_vector_weight_increased_with_description(
        self, search_service, mock_session
    ):
        """Vector weight should be > 0.5 when description provided."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
            meal_description="Zupa krem z dyni",
        )

        weight = self._get_vector_weight(mock_session)
        assert weight > 0.5, f"Expected weight > 0.5, got {weight}"

    @pytest.mark.asyncio
    async def test_no_description_keeps_balanced_weight(
        self, search_service, mock_session
    ):
        """Without description, vector weight should remain 0.5."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
        )

        weight = self._get_vector_weight(mock_session)
        assert weight == 0.5

    @pytest.mark.asyncio
    async def test_no_description_fts_uses_full_base_query(
        self, search_service, mock_session
    ):
        """Without description, FTS should include all base query keywords."""
        await search_service.search_for_meal_planning(
            session=mock_session,
            meal_type="snack",
        )

        fts_q = self._get_fts_query(mock_session)
        assert "baton" in fts_q
        assert "orzechy" in fts_q
        assert "jogurt" in fts_q
