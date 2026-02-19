"""
Unit tests for allergen filtering logic in PgVectorSearchService.

Verifies that:
- Polish morphological stems correctly match inflected word forms
- Category-based blocking works for known allergens
- Multiple allergens are checked simultaneously
- Unknown allergens fall back to simple substring matching
- Empty allergens list never blocks anything
"""
import pytest

from src.ai.infrastructure.search.pgvector_search import (
    PgVectorSearchService,
)


class TestMatchesAllergen:
    """Tests for PgVectorSearchService._matches_allergen static method."""

    # -- Egg allergen (jajko) covers Polish inflections --

    @pytest.mark.parametrize("product_name", [
        "Jajko gotowane",
        "Jajka sadzone",
        "Jajecznica na masle",
        "Jajeczny placek",
        "Omlet z warzywami",
        "Frittata wloska",
    ])
    def test_jajko_allergy_blocks_egg_products(self, product_name):
        assert PgVectorSearchService._matches_allergen(
            product_name.lower(), "", ["jajko"]
        )

    def test_jajko_allergy_does_not_block_unrelated(self):
        assert not PgVectorSearchService._matches_allergen(
            "kurczak pieczony", "", ["jajko"]
        )

    # -- Milk / lactose allergen --

    @pytest.mark.parametrize("product_name", [
        "Mleko 2%",
        "Jogurt naturalny",
        "Kefir 1.5%",
        "Smietana 18%",
        "Śmietanka do kawy",
        "Mleczko kokosowe",  # "mlecz" stem matches - expected
    ])
    def test_mleko_allergy_blocks_dairy_products(self, product_name):
        assert PgVectorSearchService._matches_allergen(
            product_name.lower(), "", ["mleko"]
        )

    # -- Gluten allergen --

    @pytest.mark.parametrize("product_name", [
        "Chleb pszenny",
        "Makaron pszenny",
        "Bułka żytnia",
        "Płatki owsiane",
        "Mąka orkiszowa",
    ])
    def test_gluten_allergy_blocks_grain_products(self, product_name):
        assert PgVectorSearchService._matches_allergen(
            product_name.lower(), "", ["gluten"]
        )

    def test_gluten_does_not_block_rice(self):
        assert not PgVectorSearchService._matches_allergen(
            "ryż biały", "", ["gluten"]
        )

    # -- Nuts allergen --

    @pytest.mark.parametrize("product_name", [
        "Orzechy włoskie",
        "Orzeszki ziemne",
        "Migdały prażone",
        "Pistacje solone",
    ])
    def test_orzechy_allergy_blocks_nut_products(self, product_name):
        assert PgVectorSearchService._matches_allergen(
            product_name.lower(), "", ["orzechy"]
        )

    # -- Category-based blocking --

    def test_jajko_allergy_blocks_by_egg_category(self):
        assert PgVectorSearchService._matches_allergen(
            "jakis produkt", "Dania z jaj", ["jajko"]
        )

    def test_jajko_allergy_blocks_by_dairy_eggs_category(self):
        assert PgVectorSearchService._matches_allergen(
            "jakis produkt", "Nabiał i jaja", ["jajko"]
        )

    def test_mleko_allergy_blocks_dairy_category(self):
        assert PgVectorSearchService._matches_allergen(
            "jakis produkt", "Nabiał", ["mleko"]
        )

    def test_gluten_allergy_blocks_bread_category(self):
        assert PgVectorSearchService._matches_allergen(
            "jakis produkt", "Pieczywo", ["gluten"]
        )

    def test_ryby_allergy_blocks_fish_category(self):
        assert PgVectorSearchService._matches_allergen(
            "jakis produkt", "Ryby", ["ryby"]
        )

    # -- Multiple allergens --

    def test_multiple_allergens_any_match_blocks(self):
        # "jajko" matches via stems, even though "gluten" doesn't
        assert PgVectorSearchService._matches_allergen(
            "jajecznica", "", ["gluten", "jajko"]
        )

    def test_multiple_allergens_none_match_allows(self):
        assert not PgVectorSearchService._matches_allergen(
            "kurczak pieczony", "Drob", ["jajko", "gluten"]
        )

    # -- Unknown allergen fallback --

    def test_unknown_allergen_uses_substring(self):
        assert PgVectorSearchService._matches_allergen(
            "sezamki", "", ["sezam"]
        )

    def test_unknown_allergen_no_match(self):
        assert not PgVectorSearchService._matches_allergen(
            "kurczak pieczony", "", ["sezam"]
        )

    # -- Edge cases --

    def test_empty_allergies_never_blocks(self):
        assert not PgVectorSearchService._matches_allergen(
            "jajecznica na masle", "Dania z jaj", []
        )

    def test_empty_name_with_category_match(self):
        assert PgVectorSearchService._matches_allergen(
            "", "Dania z jaj", ["jajko"]
        )


class TestFilterByPreferencesAllergens:
    """Tests for _filter_by_preferences with allergen stems."""

    def _make_products(self):
        return [
            {"name": "Jajecznica na masle", "category": "Dania z jaj"},
            {"name": "Kurczak pieczony", "category": "Drob"},
            {"name": "Chleb pszenny", "category": "Pieczywo"},
            {"name": "Ryz bialy", "category": "Zboza"},
            {"name": "Jogurt naturalny", "category": "Nabial"},
        ]

    def test_jajko_allergy_filters_jajecznica(self):
        service = PgVectorSearchService(embedding_service=None)
        products = self._make_products()
        filtered = service._filter_by_preferences(
            products, {"allergies": ["jajko"]}
        )
        names = [p["name"] for p in filtered]
        assert "Jajecznica na masle" not in names
        assert "Kurczak pieczony" in names
        assert "Ryz bialy" in names

    def test_gluten_allergy_filters_bread(self):
        service = PgVectorSearchService(embedding_service=None)
        products = self._make_products()
        filtered = service._filter_by_preferences(
            products, {"allergies": ["gluten"]}
        )
        names = [p["name"] for p in filtered]
        assert "Chleb pszenny" not in names
        assert "Ryz bialy" in names

    def test_multiple_allergens_filter_all(self):
        service = PgVectorSearchService(embedding_service=None)
        products = self._make_products()
        filtered = service._filter_by_preferences(
            products, {"allergies": ["jajko", "gluten", "mleko"]}
        )
        names = [p["name"] for p in filtered]
        assert "Jajecznica na masle" not in names
        assert "Chleb pszenny" not in names
        assert "Jogurt naturalny" not in names
        assert "Kurczak pieczony" in names
        assert "Ryz bialy" in names

    def test_no_allergies_passes_all(self):
        service = PgVectorSearchService(embedding_service=None)
        products = self._make_products()
        filtered = service._filter_by_preferences(
            products, {"allergies": []}
        )
        assert len(filtered) == len(products)
