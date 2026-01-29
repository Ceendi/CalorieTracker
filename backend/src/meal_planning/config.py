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

Zasady roznorodnosci (BARDZO WAZNE):
1. Ten sam typ posilku NIE MOZE sie powtarzac dzien po dniu (np. jesli jajecznica w poniedzialek, to we wtorek cos innego).
2. Unikaj powtarzania glownego skladnika (np. kurczak) czesciej niz raz na 2 dni.
3. Zadbaj o urozmaicenie zrodel bialka (jajka, nabial, mieso, ryby, roslinne).

Dla kazdego dnia podaj krotki opis posilku (np. "Owsianka z bananem", "Zupa pomidorowa").

Odpowiedz w formacie JSON:
{{"days": [{{"day": 1, "meals": [{{"type": "breakfast", "description": "..."}}, {{"type": "second_breakfast", "description": "..."}}, {{"type": "lunch", "description": "..."}}, {{"type": "snack", "description": "..."}}, {{"type": "dinner", "description": "..."}}]}}]}}"""


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

MAX_TOKENS_TEMPLATES: int = 2048
MAX_TOKENS_MEAL: int = 512
TEMPERATURE: float = 0.7

# Context size limits (Bielik has n_ctx=2048, likely supports more with RoPE scaling but keeping safe)
MAX_PRODUCTS_IN_PROMPT: int = 50   # Increased from 12 to 50
MAX_USED_INGREDIENTS_IN_PROMPT: int = 30 # Increased from 15 to 30
