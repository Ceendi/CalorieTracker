"""
Tests for NaturalLanguageProcessor (pure logic, no mocking needed).

Target: src/ai/infrastructure/nlu/processor.py
"""

import pytest

from src.ai.infrastructure.nlu.processor import NaturalLanguageProcessor
from src.ai.domain.models import IngredientChunk


@pytest.fixture
def nlu():
    return NaturalLanguageProcessor()


# ============================================================================
# TestNormalizeText
# ============================================================================


class TestNormalizeText:
    def test_synonym_pyry_to_ziemniaki(self, nlu):
        assert "ziemniaki" in nlu.normalize_text("pyry")

    def test_synonym_kartofle_to_ziemniaki(self, nlu):
        assert "ziemniaki" in nlu.normalize_text("kartofle")

    def test_synonym_jajka_to_jajko(self, nlu):
        assert "jajko" in nlu.normalize_text("jajka")

    def test_synonym_fileta_to_piers(self, nlu):
        assert "pierś" in nlu.normalize_text("fileta")

    def test_synonym_spaghetti_to_makaron_spaghetti(self, nlu):
        result = nlu.normalize_text("spaghetti")
        assert "makaron spaghetti" in result

    def test_duplicate_word_removal_after_expansion(self, nlu):
        # "makaron spaghetti" -> synonym "spaghetti"->"makaron spaghetti"
        # could produce "makaron makaron spaghetti" which should be deduped
        result = nlu.normalize_text("makaron spaghetti")
        assert "makaron makaron" not in result
        assert "makaron spaghetti" in result

    def test_lowercase(self, nlu):
        result = nlu.normalize_text("MLEKO")
        assert result == result.lower()

    def test_empty_string(self, nlu):
        assert nlu.normalize_text("") == ""

    def test_multi_synonym_text(self, nlu):
        result = nlu.normalize_text("jajka i kartofle")
        assert "jajko" in result
        assert "ziemniaki" in result

    def test_no_synonym_passthrough(self, nlu):
        result = nlu.normalize_text("woda mineralna")
        assert "woda mineralna" == result

    def test_synonym_sera_to_ser(self, nlu):
        result = nlu.normalize_text("sera")
        assert "ser" in result

    def test_synonym_pomidory_to_pomidor(self, nlu):
        result = nlu.normalize_text("pomidory")
        assert "pomidor" in result

    def test_synonym_penne_to_makaron_penne(self, nlu):
        result = nlu.normalize_text("penne")
        assert "makaron penne" in result


# ============================================================================
# TestSplitIntoChunks
# ============================================================================


class TestSplitIntoChunks:
    def test_split_on_comma(self, nlu):
        result = nlu._split_into_chunks("jajko, mleko, chleb")
        assert len(result) == 3

    def test_split_on_semicolon(self, nlu):
        result = nlu._split_into_chunks("jajko; mleko; chleb")
        assert len(result) == 3

    def test_split_on_i_connector(self, nlu):
        result = nlu._split_into_chunks("jajko i mleko")
        assert len(result) == 2

    def test_split_on_oraz(self, nlu):
        result = nlu._split_into_chunks("jajko oraz mleko")
        assert len(result) == 2

    def test_split_on_a_takze(self, nlu):
        result = nlu._split_into_chunks("jajko a także mleko")
        assert len(result) == 2

    def test_split_on_plus(self, nlu):
        result = nlu._split_into_chunks("jajko plus mleko")
        assert len(result) == 2

    def test_filter_empty_chunks(self, nlu):
        result = nlu._split_into_chunks("jajko,,, mleko")
        assert all(c.strip() for c in result)

    def test_single_item(self, nlu):
        result = nlu._split_into_chunks("jajko")
        assert len(result) == 1
        assert result[0] == "jajko"

    def test_whitespace_stripping(self, nlu):
        result = nlu._split_into_chunks("  jajko  ,  mleko  ")
        assert result[0] == "jajko"
        assert result[1] == "mleko"


# ============================================================================
# TestExtractQuantity
# ============================================================================


class TestExtractQuantity:
    def test_numeric_grams(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("200g ryż")
        assert val == 200.0
        assert unit == "g"

    def test_numeric_ml(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("250ml mleko")
        assert val == 250.0
        assert unit == "ml"

    def test_numeric_kg(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("1kg ziemniaki")
        assert val == 1.0
        assert unit == "kg"

    def test_numeric_sztuki(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("3 sztuki jajko")
        assert val == 3.0
        assert "sztuki" in unit

    def test_pol_szklanki(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("pół szklanki mleko")
        assert val == 0.5
        assert "szklanki" in unit

    def test_standalone_szklanka(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("szklanka mleko")
        assert val == 1.0
        assert "szklanka" in unit.lower()

    def test_standalone_lyzka(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("łyżka cukru")
        assert val == 1.0
        assert "łyżka" in unit.lower()

    def test_standalone_garsc(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("garść orzechów")
        assert val == 1.0
        assert "garść" in unit.lower()

    def test_decimal_with_comma(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("1,5g soli")
        assert val == 1.5
        assert unit == "g"

    def test_no_quantity_returns_none(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("kurczak")
        assert val is None
        assert unit is None

    def test_cleaned_text_after_extraction(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("200g ryż")
        assert "200" not in cleaned
        assert "ryż" in cleaned

    def test_gramy_unit(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("150 gramy mięsa")
        assert val == 150.0

    def test_gramow_unit(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("150 gramów mięsa")
        assert val == 150.0

    def test_mililitrow_unit(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("250 mililitrów wody")
        assert val == 250.0

    def test_kromka(self, nlu):
        cleaned, val, unit = nlu._extract_quantity("kromka chleba")
        assert val == 1.0
        assert "kromka" in unit.lower()


# ============================================================================
# TestExtractPolishNumeral
# ============================================================================


class TestExtractPolishNumeral:
    def test_dwa(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("dwa jajka")
        assert val == 2.0

    def test_trzy(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("trzy banany")
        assert val == 3.0

    def test_pol(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("pół jabłka")
        assert val == 0.5

    def test_poltorej(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("półtorej łyżki")
        assert val == 1.5

    def test_kilka(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("kilka plasterków")
        assert val == 3.0

    def test_pare(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("parę kromek")
        assert val == 2.0

    def test_piec(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("pięć jabłek")
        assert val == 5.0

    def test_jedna(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("jedna bułka")
        assert val == 1.0

    def test_no_numeral_returns_original(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("kurczak grillowany")
        assert val is None
        assert cleaned == "kurczak grillowany"

    def test_cleaned_text_removes_numeral(self, nlu):
        cleaned, val = nlu._extract_polish_numeral("dwa jajka")
        assert "dwa" not in cleaned
        assert "jajka" in cleaned


# ============================================================================
# TestHandleCompositeDish
# ============================================================================


class TestHandleCompositeDish:
    def test_kanapka_expands(self, nlu):
        result = nlu._handle_composite_dish("kanapka")
        assert "chleb żytni" in result
        assert "masło" in result

    def test_kanapka_z_serem(self, nlu):
        result = nlu._handle_composite_dish("kanapka z serem")
        assert "chleb żytni" in result
        assert "masło" in result
        assert "serem" in result or "ser" in " ".join(result)

    def test_jajecznica_expands(self, nlu):
        result = nlu._handle_composite_dish("jajecznica")
        assert "jajko" in result
        assert "masło" in result

    def test_owsianka_expands(self, nlu):
        result = nlu._handle_composite_dish("owsianka")
        assert "płatki owsiane" in result
        assert "mleko" in result

    def test_non_composite_returns_as_is(self, nlu):
        result = nlu._handle_composite_dish("kurczak")
        assert result == ["kurczak"]

    def test_extras_with_i_connector(self, nlu):
        result = nlu._handle_composite_dish("kanapka z serem i szynką")
        assert len(result) >= 4  # chleb, maslo, ser, szynka

    def test_kanapki_plural(self, nlu):
        result = nlu._handle_composite_dish("kanapki")
        assert "chleb żytni" in result
        assert "masło" in result

    def test_owsianki_plural(self, nlu):
        result = nlu._handle_composite_dish("owsianki")
        assert "płatki owsiane" in result


# ============================================================================
# TestVerifyKeywordConsistency
# ============================================================================


class TestVerifyKeywordConsistency:
    def test_kurczak_matches_piers_z_kurczaka(self, nlu):
        assert nlu.verify_keyword_consistency("kurczak", "pierś z kurczaka") is True

    def test_kurczak_does_not_match_ser(self, nlu):
        assert nlu.verify_keyword_consistency("kurczak", "ser żółty") is False

    def test_neither_has_keyword_passes(self, nlu):
        assert nlu.verify_keyword_consistency("woda", "herbata") is True

    def test_kurczak_vs_indyk_fails(self, nlu):
        # "kurczak" query should not match "indyk" product
        assert nlu.verify_keyword_consistency("kurczak", "indyk") is False

    def test_maslo_regex_pattern(self, nlu):
        assert nlu.verify_keyword_consistency("masło", "masło extra") is True

    def test_pomidor_regex_pattern(self, nlu):
        assert nlu.verify_keyword_consistency("pomidor", "pomidor malinowy") is True

    def test_ogorek_regex_pattern(self, nlu):
        assert nlu.verify_keyword_consistency("ogórek", "ogórek kiszony") is True

    def test_empty_strings_pass(self, nlu):
        assert nlu.verify_keyword_consistency("", "") is True

    def test_product_has_keyword_query_doesnt_fails(self, nlu):
        # Reverse guard: product says "kurczak" but query doesn't
        assert nlu.verify_keyword_consistency("ryż biały", "ryż z kurczakiem") is False

    def test_makaron_consistency(self, nlu):
        assert nlu.verify_keyword_consistency("makaron", "makaron penne") is True

    def test_ryz_consistency(self, nlu):
        assert nlu.verify_keyword_consistency("ryż", "ryż biały") is True

    def test_case_insensitive(self, nlu):
        assert nlu.verify_keyword_consistency("KURCZAK", "Pierś z kurczaka") is True


# ============================================================================
# TestProcessText
# ============================================================================


class TestProcessText:
    def test_empty_returns_empty(self, nlu):
        result = nlu.process_text("")
        assert result == []

    def test_single_ingredient(self, nlu):
        result = nlu.process_text("mleko")
        assert len(result) == 1
        assert isinstance(result[0], IngredientChunk)
        assert "mleko" in result[0].text_for_search

    def test_multiple_with_connectors(self, nlu):
        result = nlu.process_text("jajko i mleko")
        assert len(result) == 2

    def test_composite_expansion(self, nlu):
        result = nlu.process_text("kanapka")
        # kanapka -> [chleb żytni, masło], so > 1 chunk
        assert len(result) > 1

    def test_quantity_extraction_in_pipeline(self, nlu):
        result = nlu.process_text("200g ryżu")
        assert len(result) == 1
        assert result[0].quantity_value == 200.0

    def test_synonym_and_numeral_combined(self, nlu):
        result = nlu.process_text("dwa jajka")
        assert len(result) >= 1
        # After synonym: jajka -> jajko, after numeral: dwa -> 2.0
        chunk = result[0]
        assert chunk.quantity_value == 2.0

    def test_complex_meal_description(self, nlu):
        result = nlu.process_text("200g ryżu, pierś z kurczaka i sałatka")
        assert len(result) >= 3

    def test_is_composite_flag(self, nlu):
        result = nlu.process_text("kanapka")
        composite_chunks = [c for c in result if c.is_composite]
        assert len(composite_chunks) > 0

    def test_non_composite_flag(self, nlu):
        result = nlu.process_text("mleko")
        assert result[0].is_composite is False

    def test_quantity_unit_extracted(self, nlu):
        result = nlu.process_text("250ml mleka")
        assert result[0].quantity_unit == "ml"

    def test_original_text_preserved(self, nlu):
        result = nlu.process_text("mleko")
        assert result[0].original_text is not None
        assert len(result[0].original_text) > 0
