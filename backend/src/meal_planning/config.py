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
# TEMPLATE GENERATION PROMPT
# =============================================================================

TEMPLATE_GENERATION_PROMPT: str = """Zaplanuj strukture {days} dni posilkow dla osoby o zapotrzebowaniu {kcal} kcal dziennie.

Rozklad kalorii:
- Sniadanie: 25% ({breakfast_kcal} kcal)
- II sniadanie: 10% ({snack1_kcal} kcal)
- Obiad: 35% ({lunch_kcal} kcal)
- Podwieczorek: 10% ({snack2_kcal} kcal)
- Kolacja: 20% ({dinner_kcal} kcal)

Preferencje: {preferences}

Dla kazdego dnia podaj krotki opis posilku (np. "Owsianka z bananem", "Zupa pomidorowa").
Zadbaj o roznorodnosc miedzy dniami.

Odpowiedz w formacie JSON:
{{"days": [{{"day": 1, "meals": [{{"type": "breakfast", "description": "..."}}, {{"type": "second_breakfast", "description": "..."}}, {{"type": "lunch", "description": "..."}}, {{"type": "snack", "description": "..."}}, {{"type": "dinner", "description": "..."}}]}}]}}"""


# =============================================================================
# MEAL GENERATION PROMPT
# =============================================================================

MEAL_GENERATION_PROMPT: str = """Stworz przepis: {description}

Cel kaloryczny: ~{target_kcal} kcal
Makro: B:{target_protein}g, T:{target_fat}g, W:{target_carbs}g

Dostepne produkty (uzywaj TYLKO tych):
{products}

Ostatnio uzyte (unikaj): {used}

Odpowiedz w JSON:
{{"name": "...", "description": "krotki opis", "preparation_time": 15, "ingredients": [{{"name": "nazwa z listy", "amount_grams": 100, "unit_label": "1 szklanka"}}]}}"""


# =============================================================================
# MODEL PARAMETERS
# =============================================================================

MAX_TOKENS_TEMPLATES: int = 1024
MAX_TOKENS_MEAL: int = 512
TEMPERATURE: float = 0.7

# Context size limits (Bielik has n_ctx=2048)
MAX_PRODUCTS_IN_PROMPT: int = 12
MAX_USED_INGREDIENTS_IN_PROMPT: int = 15
