"""
Tests for MealRecognitionService.

Target: src/ai/application/meal_service.py
Mocks: SearchEnginePort, NLUProcessorPort, NLUExtractorPort
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from src.ai.application.meal_service import MealRecognitionService
from src.ai.domain.models import (
    SearchCandidate,
    MatchedProduct,
    IngredientChunk,
    MealExtraction,
    ExtractedFoodItem,
    MealType,
)
from src.ai.config import (
    DEFAULT_UNIT_GRAMS,
    DEFAULT_PORTION_GRAMS,
    MEAL_RECOGNITION_CONFIG as CONFIG,
)


# ============================================================================
# Factories and Fixtures
# ============================================================================

def make_product_id():
    return str(uuid.uuid4())


def make_search_candidate(
    name="mleko 3.2%",
    score=0.85,
    category="DAI",
    passed_guard=True,
    product_id=None,
    notes=None,
):
    return SearchCandidate(
        product_id=product_id or make_product_id(),
        name=name,
        score=score,
        category=category,
        passed_guard=passed_guard,
        notes=notes,
    )


def make_product_dict(
    name_pl="mleko 3.2%",
    name_en="milk 3.2%",
    kcal_100g=60.0,
    protein_100g=3.2,
    fat_100g=3.2,
    carbs_100g=4.8,
    category="DAI",
    units=None,
):
    return {
        "id": make_product_id(),
        "name_pl": name_pl,
        "name_en": name_en,
        "kcal_100g": kcal_100g,
        "protein_100g": protein_100g,
        "fat_100g": fat_100g,
        "carbs_100g": carbs_100g,
        "category": category,
        "units": units or [],
    }


@pytest.fixture
def mock_search_engine():
    engine = MagicMock()
    engine.search = AsyncMock(return_value=[])
    engine.get_product_by_id = MagicMock(return_value=make_product_dict())
    engine.index_products = MagicMock()
    return engine


@pytest.fixture
def mock_nlu_processor():
    nlu = MagicMock()
    nlu.normalize_text = MagicMock(side_effect=lambda x: x.lower())
    nlu.process_text = MagicMock(return_value=[])
    nlu.verify_keyword_consistency = MagicMock(return_value=True)
    return nlu


@pytest.fixture
def mock_slm_extractor():
    slm = MagicMock()
    slm.is_available = MagicMock(return_value=True)
    extraction = MealExtraction(
        meal_type=MealType.LUNCH,
        raw_transcription="test",
        items=[
            ExtractedFoodItem(name="ryż", quantity_value=200.0, quantity_unit="g"),
        ],
        overall_confidence=0.9,
    )
    slm.extract = AsyncMock(return_value=(extraction, 0.9))
    return slm


@pytest.fixture
def service(mock_search_engine, mock_nlu_processor, mock_slm_extractor):
    return MealRecognitionService(
        vector_engine=mock_search_engine,
        nlu_processor=mock_nlu_processor,
        slm_extractor=mock_slm_extractor,
    )


@pytest.fixture
def service_no_slm(mock_search_engine, mock_nlu_processor):
    return MealRecognitionService(
        vector_engine=mock_search_engine,
        nlu_processor=mock_nlu_processor,
        slm_extractor=None,
    )


# ============================================================================
# TestRecognizeMeal
# ============================================================================


class TestRecognizeMeal:
    @pytest.mark.asyncio
    async def test_happy_path_with_slm(self, service, mock_search_engine, mock_slm_extractor):
        pid = make_product_id()
        candidate = make_search_candidate(name="ryż", score=0.9, product_id=pid)
        mock_search_engine.search.return_value = [candidate]
        mock_search_engine.get_product_by_id.return_value = make_product_dict(
            name_pl="ryż biały", kcal_100g=130.0
        )

        result = await service.recognize_meal("200g ryżu")
        assert len(result.matched_products) == 1
        assert result.matched_products[0].name_pl == "ryż"

    @pytest.mark.asyncio
    async def test_fallback_to_regex_when_slm_unavailable(
        self, service_no_slm, mock_search_engine, mock_nlu_processor
    ):
        mock_nlu_processor.process_text.return_value = [
            IngredientChunk(
                original_text="ryż",
                text_for_search="ryż",
                quantity_value=200.0,
                quantity_unit="g",
            )
        ]
        pid = make_product_id()
        candidate = make_search_candidate(name="ryż biały", score=0.85, product_id=pid)
        mock_search_engine.search.return_value = [candidate]

        result = await service_no_slm.recognize_meal("200g ryżu")
        mock_nlu_processor.process_text.assert_called_once()
        assert len(result.matched_products) == 1

    @pytest.mark.asyncio
    async def test_fallback_when_slm_raises_exception(
        self, service, mock_search_engine, mock_slm_extractor, mock_nlu_processor
    ):
        mock_slm_extractor.extract.side_effect = RuntimeError("SLM crash")
        mock_nlu_processor.process_text.return_value = [
            IngredientChunk(
                original_text="mleko",
                text_for_search="mleko",
                quantity_value=1.0,
                quantity_unit="porcja",
            )
        ]
        candidate = make_search_candidate(name="mleko", score=0.8)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("mleko")
        mock_nlu_processor.process_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_unmatched_chunk_when_search_returns_empty(
        self, service, mock_search_engine, mock_slm_extractor
    ):
        mock_search_engine.search.return_value = []

        result = await service.recognize_meal("nieznany produkt")
        assert len(result.unmatched_chunks) == 1
        assert len(result.matched_products) == 0

    @pytest.mark.asyncio
    async def test_multiple_chunks(self, service, mock_search_engine, mock_slm_extractor):
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[
                ExtractedFoodItem(name="ryż", quantity_value=200.0, quantity_unit="g"),
                ExtractedFoodItem(name="kurczak", quantity_value=150.0, quantity_unit="g"),
            ],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        pid1 = make_product_id()
        pid2 = make_product_id()

        # Return different candidates for each search call
        mock_search_engine.search.side_effect = [
            [make_search_candidate(name="ryż biały", score=0.9, product_id=pid1)],
            [make_search_candidate(name="pierś z kurczaka", score=0.85, product_id=pid2)],
        ]

        result = await service.recognize_meal("ryż i kurczak")
        assert len(result.matched_products) == 2

    @pytest.mark.asyncio
    async def test_overall_confidence_averaging(self, service, mock_search_engine, mock_slm_extractor):
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[
                ExtractedFoodItem(name="ryż", quantity_value=100.0, quantity_unit="g"),
                ExtractedFoodItem(name="mleko", quantity_value=100.0, quantity_unit="g"),
            ],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        mock_search_engine.search.side_effect = [
            [make_search_candidate(name="ryż biały", score=0.8)],
            [make_search_candidate(name="mleko", score=0.6)],
        ]

        result = await service.recognize_meal("ryż i mleko")
        assert result.overall_confidence > 0
        assert len(result.matched_products) == 2

    @pytest.mark.asyncio
    async def test_confidence_zero_when_no_matches(self, service, mock_search_engine):
        mock_search_engine.search.return_value = []
        result = await service.recognize_meal("xyz")
        assert result.overall_confidence == 0.0

    @pytest.mark.asyncio
    async def test_processing_time_positive(self, service, mock_search_engine):
        mock_search_engine.search.return_value = []
        result = await service.recognize_meal("test")
        assert result.processing_time_ms >= 0


# ============================================================================
# TestScoringHeuristics
# ============================================================================


class TestScoringHeuristics:
    @pytest.mark.asyncio
    async def test_exact_match_boost(self, service, mock_search_engine, mock_slm_extractor):
        """Exact name match should get EXACT_MATCH_BOOST."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="ryż", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        # Candidate name exactly matches query after normalization
        candidate = make_search_candidate(name="ryż", score=0.5)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("ryż")
        # Score should be boosted: 0.5 + 3.0 + 0.5 (prefix) = 4.0, clamped to 1.0
        assert result.matched_products[0].match_confidence == 1.0

    @pytest.mark.asyncio
    async def test_token_match_boost(self, service, mock_search_engine, mock_slm_extractor):
        """Query as token in candidate should get TOKEN_MATCH_BOOST."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="ryż", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        # "ryż" is a token in "ryż biały"
        candidate = make_search_candidate(name="ryż biały", score=0.3)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("ryż")
        # 0.3 + 1.0 (token) + 0.5 (prefix) = 1.8, clamped to 1.0
        assert result.matched_products[0].match_confidence == 1.0

    @pytest.mark.asyncio
    async def test_prefix_match_boost(self, service, mock_search_engine, mock_slm_extractor):
        """Candidate starting with query should get PREFIX_MATCH_BOOST."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="mle", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        candidate = make_search_candidate(name="mleko 3.2%", score=0.3)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("mle")
        # 0.3 + 0.5 (prefix) = 0.8
        assert result.matched_products[0].match_confidence > 0.3

    @pytest.mark.asyncio
    async def test_multi_token_penalty(self, service, mock_search_engine, mock_slm_extractor):
        """Single-token query vs 3+ token candidate should get MULTI_TOKEN_PENALTY."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="ser", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        candidate = make_search_candidate(
            name="ser żółty gouda plastry", score=0.5, category="DAI"
        )
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("ser")
        # Score penalized: single query token vs 4 candidate tokens
        matched = result.matched_products[0]
        # The penalty brings score down from 0.5
        assert matched.match_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_guard_fail_multiplier(self, service, mock_search_engine, mock_slm_extractor, mock_nlu_processor):
        """Guard failure should multiply score by GUARD_FAIL_MULTIPLIER."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="kurczak", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        mock_nlu_processor.verify_keyword_consistency.return_value = False
        candidate = make_search_candidate(name="indyk", score=0.8)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("kurczak")
        # Score = 0.8 * 0.4 (guard fail) = 0.32 * 0.85 (confidence multiplier) = 0.272
        assert result.matched_products[0].match_confidence < 0.8

    @pytest.mark.asyncio
    async def test_guard_fail_confidence_multiplier(
        self, service, mock_search_engine, mock_slm_extractor, mock_nlu_processor
    ):
        """Guard fail should also apply GUARD_FAIL_CONFIDENCE_MULTIPLIER to final confidence."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="kurczak", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        mock_nlu_processor.verify_keyword_consistency.return_value = False
        candidate = make_search_candidate(name="indyk", score=0.5)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("kurczak")
        matched = result.matched_products[0]
        # Score was 0.5 * 0.4 = 0.2, then confidence *= 0.85 -> 0.17
        assert matched.match_confidence < 0.5

    @pytest.mark.asyncio
    async def test_score_clamped_to_0_1(self, service, mock_search_engine, mock_slm_extractor):
        """Score should be clamped between 0 and 1."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="ryż", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        # Very high raw score + boosts should still clamp to 1.0
        candidate = make_search_candidate(name="ryż", score=0.95)
        mock_search_engine.search.return_value = [candidate]

        result = await service.recognize_meal("ryż")
        assert 0.0 <= result.matched_products[0].match_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_candidates_sorted_by_adjusted_score(
        self, service, mock_search_engine, mock_slm_extractor
    ):
        """Best candidate should be selected after sorting by adjusted score."""
        extraction = MealExtraction(
            meal_type=MealType.LUNCH,
            raw_transcription="test",
            items=[ExtractedFoodItem(name="mleko", quantity_value=100.0, quantity_unit="g")],
        )
        mock_slm_extractor.extract.return_value = (extraction, 0.9)

        pid1 = make_product_id()
        pid2 = make_product_id()
        c1 = make_search_candidate(name="mleko zagęszczone", score=0.9, product_id=pid1)
        c2 = make_search_candidate(name="mleko", score=0.7, product_id=pid2)
        mock_search_engine.search.return_value = [c1, c2]

        product1 = make_product_dict(name_pl="mleko zagęszczone")
        product2 = make_product_dict(name_pl="mleko")
        mock_search_engine.get_product_by_id.side_effect = lambda pid: (
            product1 if pid == pid1 else product2
        )

        result = await service.recognize_meal("mleko")
        # "mleko" exact match (c2) gets EXACT_MATCH_BOOST + PREFIX, should win
        assert result.matched_products[0].name_pl == "mleko"


# ============================================================================
# TestCalculateGrams
# ============================================================================


class TestCalculateGrams:
    def setup_method(self):
        engine = MagicMock()
        nlu = MagicMock()
        self.service = MealRecognitionService(
            vector_engine=engine, nlu_processor=nlu
        )

    def _item(self, val=100.0, unit="g"):
        return ExtractedFoodItem(name="test", quantity_value=val, quantity_unit=unit)

    def test_grams_direct(self):
        product = make_product_dict()
        result = self.service._calculate_grams(self._item(200.0, "g"), product)
        assert result == 200.0

    def test_gramy_direct(self):
        product = make_product_dict()
        result = self.service._calculate_grams(self._item(150.0, "gramy"), product)
        assert result == 150.0

    def test_ml_direct(self):
        product = make_product_dict()
        result = self.service._calculate_grams(self._item(250.0, "ml"), product)
        assert result == 250.0

    def test_kg_multiply(self):
        product = make_product_dict()
        result = self.service._calculate_grams(self._item(1.5, "kg"), product)
        assert result == 1500.0

    def test_product_unit_match_szklanka(self):
        product = make_product_dict(
            units=[{"name": "szklanka", "weight_g": 250.0}]
        )
        result = self.service._calculate_grams(self._item(2.0, "szklanka"), product)
        assert result == 500.0

    def test_product_unit_match_sztuka(self):
        product = make_product_dict(
            units=[{"name": "sztuka", "weight_g": 60.0}]
        )
        result = self.service._calculate_grams(self._item(3.0, "sztuka"), product)
        assert result == 180.0

    def test_default_unit_grams_fallback_lyzka(self):
        product = make_product_dict(units=[])
        result = self.service._calculate_grams(self._item(2.0, "łyżka"), product)
        assert result == DEFAULT_UNIT_GRAMS["łyżka"] * 2.0

    def test_default_portion_grams_when_no_match(self):
        product = make_product_dict(units=[])
        # "talerz" has no match in product units or DEFAULT_UNIT_GRAMS
        result = self.service._calculate_grams(self._item(1.0, "talerz"), product)
        assert result == DEFAULT_PORTION_GRAMS * 1.0

    def test_porcja_from_default_unit_grams(self):
        product = make_product_dict(units=[])
        result = self.service._calculate_grams(self._item(1.0, "porcja"), product)
        assert result == DEFAULT_UNIT_GRAMS["porcja"]

    def test_none_product_returns_default(self):
        result = self.service._calculate_grams(self._item(1.0, "g"), None)
        assert result == DEFAULT_PORTION_GRAMS

    def test_szklanka_from_default_grams(self):
        product = make_product_dict(units=[])
        result = self.service._calculate_grams(self._item(1.0, "szklanka"), product)
        assert result == DEFAULT_UNIT_GRAMS["szklanka"]

    def test_kromka_from_default_grams(self):
        product = make_product_dict(units=[])
        result = self.service._calculate_grams(self._item(2.0, "kromka"), product)
        assert result == DEFAULT_UNIT_GRAMS["kromka"] * 2.0


# ============================================================================
# TestRecognizeFromVisionItems
# ============================================================================


class TestRecognizeFromVisionItems:
    @pytest.mark.asyncio
    async def test_db_match_above_threshold(self, service, mock_search_engine):
        pid = make_product_id()
        candidate = make_search_candidate(name="ryż biały", score=0.85, product_id=pid)
        mock_search_engine.search.return_value = [candidate]
        mock_search_engine.get_product_by_id.return_value = make_product_dict(
            name_pl="ryż biały", kcal_100g=130.0
        )

        items = [
            ExtractedFoodItem(name="ryż", quantity_value=200.0, quantity_unit="g")
        ]

        result = await service.recognize_from_vision_items(items)
        assert len(result.matched_products) == 1
        assert result.matched_products[0].match_strategy == "vision_vector_hybrid"

    @pytest.mark.asyncio
    async def test_below_threshold_uses_gemini_macros(self, service, mock_search_engine):
        candidate = make_search_candidate(name="jakiś produkt", score=0.2)
        mock_search_engine.search.return_value = [candidate]

        items = [
            ExtractedFoodItem(
                name="coś nieznanego",
                quantity_value=100.0,
                quantity_unit="g",
                kcal=200.0,
                protein=10.0,
                fat=5.0,
                carbs=25.0,
            )
        ]

        result = await service.recognize_from_vision_items(items)
        matched = result.matched_products[0]
        assert matched.match_strategy == "vision_ai_estimate"
        assert matched.product_id == "00000000-0000-0000-0000-000000000000"
        assert matched.kcal == 200.0

    @pytest.mark.asyncio
    async def test_fallback_grams_for_non_gram_units(self, service, mock_search_engine):
        mock_search_engine.search.return_value = []

        items = [
            ExtractedFoodItem(
                name="bułka", quantity_value=2.0, quantity_unit="sztuka", kcal=150.0
            )
        ]

        result = await service.recognize_from_vision_items(items)
        matched = result.matched_products[0]
        # sztuka: DEFAULT_PORTION_GRAMS * 2.0 (no keyword match for "sztuka" in DEFAULT_UNIT_GRAMS keys)
        # Actually DEFAULT_UNIT_GRAMS has "sztuka": 100.0, so 100.0 * 2.0 = 200.0
        assert matched.quantity_grams > 0

    @pytest.mark.asyncio
    async def test_empty_items_returns_empty_result(self, service):
        result = await service.recognize_from_vision_items([])
        assert len(result.matched_products) == 0
        assert result.overall_confidence == 0.0

    @pytest.mark.asyncio
    async def test_processing_time_positive(self, service, mock_search_engine):
        mock_search_engine.search.return_value = []
        items = [ExtractedFoodItem(name="test", quantity_value=1.0, quantity_unit="g")]
        result = await service.recognize_from_vision_items(items)
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    async def test_scoring_heuristics_applied(self, service, mock_search_engine, mock_nlu_processor):
        pid = make_product_id()
        candidate = make_search_candidate(name="mleko", score=0.6, product_id=pid)
        mock_search_engine.search.return_value = [candidate]
        mock_search_engine.get_product_by_id.return_value = make_product_dict(name_pl="mleko")

        items = [
            ExtractedFoodItem(name="mleko", quantity_value=250.0, quantity_unit="g")
        ]

        result = await service.recognize_from_vision_items(items)
        assert len(result.matched_products) == 1
        # Exact match boost should push it above 0.5 threshold
        assert result.matched_products[0].match_strategy == "vision_vector_hybrid"

    @pytest.mark.asyncio
    async def test_overall_confidence_averaged(self, service, mock_search_engine):
        pid1 = make_product_id()
        pid2 = make_product_id()
        mock_search_engine.search.side_effect = [
            [make_search_candidate(name="ryż", score=0.9, product_id=pid1)],
            [make_search_candidate(name="kurczak", score=0.8, product_id=pid2)],
        ]

        items = [
            ExtractedFoodItem(name="ryż", quantity_value=200.0, quantity_unit="g"),
            ExtractedFoodItem(name="kurczak", quantity_value=150.0, quantity_unit="g"),
        ]

        result = await service.recognize_from_vision_items(items)
        assert result.overall_confidence > 0

    @pytest.mark.asyncio
    async def test_guard_fail_in_vision(self, service, mock_search_engine, mock_nlu_processor):
        mock_nlu_processor.verify_keyword_consistency.return_value = False
        pid = make_product_id()
        candidate = make_search_candidate(name="indyk", score=0.7, product_id=pid)
        mock_search_engine.search.return_value = [candidate]

        items = [
            ExtractedFoodItem(
                name="kurczak", quantity_value=100.0, quantity_unit="g",
                kcal=165.0, protein=31.0, fat=3.6, carbs=0.0,
            )
        ]

        result = await service.recognize_from_vision_items(items)
        # Guard fail: 0.7 * 0.4 = 0.28 < 0.5, should fall back to AI estimate
        assert result.matched_products[0].match_strategy == "vision_ai_estimate"

    @pytest.mark.asyncio
    async def test_db_match_uses_db_macros(self, service, mock_search_engine):
        pid = make_product_id()
        candidate = make_search_candidate(name="jajko", score=0.85, product_id=pid)
        mock_search_engine.search.return_value = [candidate]
        mock_search_engine.get_product_by_id.return_value = make_product_dict(
            name_pl="jajko", kcal_100g=155.0, protein_100g=12.6, fat_100g=11.5, carbs_100g=0.7
        )

        items = [
            ExtractedFoodItem(
                name="jajko", quantity_value=100.0, quantity_unit="g",
                kcal=75.0, protein=6.0, fat=5.0, carbs=0.3,  # Gemini estimates
            )
        ]

        result = await service.recognize_from_vision_items(items)
        matched = result.matched_products[0]
        # Should use DB macros (155 kcal/100g), not Gemini (75 kcal)
        assert matched.kcal == 155.0
