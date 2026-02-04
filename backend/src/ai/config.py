from dataclasses import dataclass
from typing import Any, Dict, FrozenSet


# ============================================================================
# WHISPER STT CONFIGURATION
# ============================================================================

WHISPER_INITIAL_PROMPT: str = (
    "Opis posiłku po polsku. Zjadłem na śniadanie kanapkę z szynką i serem, "
    "obiad, kolację. Produkty spożywcze: jajka, mleko, chleb, masło, ser żółty, "
    "szynka, pomidor, ogórek, jabłko, banan, ryż, makaron, kurczak, pierś z kurczaka."
)

WHISPER_CONFIG: Dict[str, Any] = {
    "fp16": False,
    "verbose": False,
    "beam_size": 5,
    "best_of": 5,
    "temperature": 0.0,
}


# ============================================================================
# SLM (BIELIK) NLU CONFIGURATION
# ============================================================================

SLM_SYSTEM_PROMPT: str = (
    "Jesteś precyzyjnym asystentem dietetycznym. Twoim zadaniem jest ekstrakcja składników posiłków z tekstu "
    "w formacie JSON.\n"
    "Zasady:\n"
    "1. Rozbijaj dania składane (np. 'kanapka z serem' -> chleb, masło, ser). NIE rozbijaj dań gotowych (np. "
    "'Bigos', 'Pierogi', 'Mizeria').\n"
    "2. Ignoruj składniki wykluczone (np. 'bez cukru' -> nie dodawaj cukru).\n"
    "3. Zamieniaj liczebniki słowne na liczby (np. 'dwa' -> 2, 'pół' -> 0.5).\n"
    "4. Domyślne ilości: 'trochę' = 50g, 'dużo' = 150g, 'szklanka' = 250ml, 'łyżka' = 15g, 'łyżeczka' = 5g.\n"
    "5. 'Plaster', 'kromka', 'kawałek' -> zamieniaj na 'sztuka'. 'Chleb' -> 'Chleb żytni'.\n"
    "6. Dla 'ziemniaków' bez formy przyjmij 'ziemniak gotowany'. 'Omlet' to jajka i masło.\n"
    "7. Typ posiłku: śniadanie, drugie_śniadanie, obiad, podwieczorek, kolacja, lub przekąska."
)

SLM_MAX_TOKENS: int = 512
SLM_TEMPERATURE: float = 0.1


# ============================================================================
# MEAL RECOGNITION SCORING CONFIGURATION
# ============================================================================

@dataclass(frozen=True)
class MealRecognitionConfig:
    EXACT_MATCH_BOOST: float = 3.0
    TOKEN_MATCH_BOOST: float = 1.0
    PREFIX_MATCH_BOOST: float = 0.5
    MULTI_TOKEN_PENALTY: float = 0.5
    DERIVATIVE_PENALTY_MULTIPLIER: float = 0.3
    FRESH_CATEGORY_BOOST: float = 0.3
    GUARD_FAIL_MULTIPLIER: float = 0.4
    GUARD_FAIL_CONFIDENCE_MULTIPLIER: float = 0.85

    # Increased from 0.2 to 0.5 to give more weight to vector search (E5)
    # E5 handles Polish morphology better than BM25 without a stemmer
    HYBRID_SEARCH_ALPHA: float = 0.5


DERIVATIVE_KEYWORDS: FrozenSet[str] = frozenset({
    "mąka", "skrobia", "płatki", "chleb", "bułka", "puree", "placki", "chipsy", "frytki",
    "halloumi", "białko", "białka", "żółtko", "żółtka", "proszek", "pasta", "mix",
    "czekolada", "czekoladowe", "wanilia", "waniliowe", "truskawka", "truskawkowe", "kakao", "kakaowe",
    "topiony", "wędzony"
})

FRESH_CATEGORIES: FrozenSet[str] = frozenset({
    "VEGFRESH", "FRUIFRESH", "DAI", "EGGS", "MEAT", "VEGPOT", "VEGROOT", "FISH"
})

DEFAULT_UNIT_GRAMS: Dict[str, float] = {
    # Containers / measures
    "szklanka": 250.0,
    "szklankę": 250.0,
    "szklanki": 250.0,
    "łyżka": 15.0,
    "łyżkę": 15.0,
    "łyżki": 15.0,
    "łyżeczka": 5.0,
    "łyżeczkę": 5.0,
    "łyżeczki": 5.0,

    # Bread portions
    "kromka": 35.0,
    "kromkę": 35.0,
    "kromki": 35.0,
    "plaster": 20.0,
    "plasterek": 20.0,
    "plastry": 20.0,
    "plasterki": 20.0,

    # Countable units
    "sztuka": 100.0,
    "sztuki": 100.0,
    "sztuk": 100.0,
    "szt": 100.0,

    # Approximate amounts
    "garść": 30.0,
    "porcja": 150.0,
    "porcję": 150.0,
    "porcji": 150.0,

    # Descriptive quantities
    "dużo": 150.0,
    "mało": 50.0,
    "trochę": 50.0,
    "odrobina": 10.0,
    "szczypta": 2.0,
}

MEAL_TYPE_KEYWORDS: Dict[str, str] = {
    "śniadanie": "breakfast",
    "obiad": "lunch",
    "zup": "lunch",
    "kolacj": "dinner"
}

DEFAULT_MEAL_TYPE: str = "snack"

DEFAULT_PORTION_GRAMS: float = 100.0


MEAL_RECOGNITION_CONFIG = MealRecognitionConfig()
