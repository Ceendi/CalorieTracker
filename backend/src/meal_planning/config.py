"""
Configuration for meal planning LLM adapter.

Contains system prompts, generation prompts, and model parameters
for the Bielik-based meal planner.
"""

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

MEAL_PLANNER_SYSTEM_PROMPT: str = """Jestes polskim dietetykiem i kucharzem. Tworzysz zdrowe, smaczne plany zywieniowe.
Zasady:
1. Uzywaj TYLKO produktow z podanej listy dostepnych skladnikow.
2. Komponuj posilki typowe dla polskiej kuchni.
3. Dbaj o roznorodnosc - nie powtarzaj tych samych skladnikow zbyt czesto.
4. Podawaj realistyczne gramatury.
5. Odpowiadaj TYLKO w formacie JSON."""


# =============================================================================
# TEMPLATE GENERATION PROMPT (per-day, simpler for small models)
# =============================================================================

TEMPLATE_GENERATION_PROMPT_SINGLE_DAY: str = """Zaplanuj 5 ROZNYCH posilkow na 1 dzien ({kcal} kcal).

Preferencje: {preferences}
{previous_days_context}
ZASADA: Kazdy posilek MUSI byc INNY niz wymienione wyzej. Uzyj innych skladnikow i innych dan.

Dla kazdego posilku podaj opis i 2-4 skladniki (PRODUKTY, nie nazwy dan).

Odpowiedz TYLKO JSON:
{{"meals": [{{"type": "breakfast", "description": "opis", "keywords": ["produkt1", "produkt2"]}}, {{"type": "second_breakfast", "description": "opis", "keywords": ["produkt1"]}}, {{"type": "lunch", "description": "opis", "keywords": ["produkt1", "produkt2"]}}, {{"type": "snack", "description": "opis", "keywords": ["produkt1"]}}, {{"type": "dinner", "description": "opis", "keywords": ["produkt1", "produkt2"]}}]}}"""

# Legacy prompt (kept for reference, not used)
TEMPLATE_GENERATION_PROMPT: str = TEMPLATE_GENERATION_PROMPT_SINGLE_DAY


# =============================================================================
# MEAL GENERATION PROMPT
# =============================================================================

MEAL_GENERATION_PROMPT: str = """Stworz przepis: "{description}"

Cel: ~{target_kcal} kcal (B:{target_protein}g, T:{target_fat}g, W:{target_carbs}g)

DOSTEPNE PRODUKTY (wybieraj TYLKO po numerze [X]):
{products}

Ostatnio uzyte (unikaj): {used}

ZASADY:
1. Wybierz 3-6 produktow po NUMERZE z listy powyzej.
2. Podaj gramatury (typowo 50-200g, dla przypraw 5-15g).
3. Suma kalorii powinna byc bliska {target_kcal} kcal.

FORMAT ODPOWIEDZI (TYLKO JSON):
{{"name": "Nazwa posilku", "description": "Krotki opis", "preparation_time": 15, "ingredients": [{{"idx": 1, "grams": 150}}, {{"idx": 3, "grams": 100}}]}}"""


# =============================================================================
# MODEL PARAMETERS
# =============================================================================

MAX_TOKENS_TEMPLATES: int = 1024  # Reduced - now generating 1 day at a time
MAX_TOKENS_MEAL: int = 512
TEMPERATURE_TEMPLATES: float = 0.5  # Lower for more consistent structure
TEMPERATURE_MEAL: float = 0.7  # Higher for creative meal names


# =============================================================================
# JSON SCHEMAS FOR GRAMMAR-BASED GENERATION
# =============================================================================

# Schema for single-day template generation
DAY_TEMPLATE_JSON_SCHEMA: str = """{
  "type": "object",
  "properties": {
    "meals": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "enum": ["breakfast", "second_breakfast", "lunch", "snack", "dinner"]},
          "description": {"type": "string"},
          "keywords": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5}
        },
        "required": ["type", "description", "keywords"]
      },
      "minItems": 5,
      "maxItems": 5
    }
  },
  "required": ["meals"]
}"""

# Schema for meal generation
MEAL_JSON_SCHEMA: str = """{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"},
    "preparation_time": {"type": "integer"},
    "ingredients": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "idx": {"type": "integer"},
          "grams": {"type": "integer"}
        },
        "required": ["idx", "grams"]
      },
      "minItems": 2,
      "maxItems": 8
    }
  },
  "required": ["name", "ingredients"]
}"""

# Context size limits (Bielik has n_ctx=2048, likely supports more with RoPE scaling but keeping safe)
MAX_PRODUCTS_IN_PROMPT: int = 50   # Increased from 12 to 50
MAX_USED_INGREDIENTS_IN_PROMPT: int = 30 # Increased from 15 to 30
