from src.food_catalogue.application.gi_utils import match_gi, _normalize


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("CHLEB BIAŁY") == "chleb bialy"

    def test_strips_diacritics(self):
        assert _normalize("zupa żółwiowa") == "zupa zolwiowa"

    def test_l_to_l_replacement(self):
        assert _normalize("biały chleb") == "bialy chleb"

    def test_removes_brand_stopword(self):
        assert _normalize("Danone jogurt owocowy") == "jogurt owocowy"

    def test_removes_nonalpha(self):
        assert _normalize("Ryż 2.5%") == "ryz 2 5"

    def test_empty_string(self):
        assert _normalize("") == ""


class TestMatchGI:
    def test_low_carb_returns_none(self):
        assert match_gi("Kurczak pierś", 0.5) is None

    def test_boundary_exactly_5g_returns_none(self):
        assert match_gi("cokolwiek", 5.0) is None

    def test_exact_match(self):
        assert match_gi("jablko", 14.0) == 36.0

    def test_substring_match_with_polish_chars(self):
        assert match_gi("Ryż biały gotowany", 28.0) == 73.0

    def test_no_match_returns_none(self):
        assert match_gi("nieznany produkt xyz", 30.0) is None

    def test_empty_name_returns_none(self):
        assert match_gi("", 20.0) is None

    def test_brand_stripped_still_matches(self):
        assert match_gi("Milka czekolada mleczna", 57.0) == 40.0

    def test_longest_key_wins(self):
        assert match_gi("Makaron pełnoziarnisty razowy", 65.0) == 48.0

    def test_atkinson_2021_entry(self):
        assert match_gi("kasza gryczana", 72.0) == 46.0

    def test_brown_rice_over_white(self):
        assert match_gi("Ryż brązowy gotowany", 23.0) == 68.0

    def test_returns_float(self):
        result = match_gi("jablko", 14.0)
        assert isinstance(result, float)
