"""
Bielik LLM Adapter for meal plan generation.

Implements MealPlannerPort using the existing Bielik 4.5B model.
Uses lazy loading and singleton pattern via SLMLoader.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger

from src.meal_planning.domain.ports import MealPlannerPort
from src.meal_planning.domain.entities import (
    UserProfile,
    MealTemplate,
    GeneratedMeal,
    GeneratedIngredient,
    GeneratedDay,
)
from src.meal_planning.config import (
    MEAL_PLANNER_SYSTEM_PROMPT,
    TEMPLATE_GENERATION_PROMPT_SINGLE_DAY,
    MEAL_GENERATION_PROMPT,
    MAX_TOKENS_TEMPLATES,
    MAX_TOKENS_MEAL,
    TEMPERATURE_TEMPLATES,
    TEMPERATURE_MEAL,
    MAX_PRODUCTS_IN_PROMPT,
    MAX_USED_INGREDIENTS_IN_PROMPT,
    DAY_TEMPLATE_JSON_SCHEMA,
    MEAL_JSON_SCHEMA,
)
from src.ai.infrastructure.embedding.embedding_service import EmbeddingService
import numpy as np


# Mapping of Polish dish name stems to their typical ingredients
# Used as fallback when LLM doesn't provide keywords
DISH_TO_INGREDIENTS: Dict[str, List[str]] = {
    # Breakfast dishes
    "kanapk": ["chleb", "pieczywo"],
    "jajecznic": ["jajko"],
    "owsiank": ["platki owsiane", "owsianka"],
    "jajecz": ["jajko"],
    "omlet": ["jajko"],
    "tost": ["chleb tostowy", "pieczywo"],
    "jogurt": ["jogurt"],
    "muesli": ["musli", "platki"],
    "granola": ["granola", "platki"],
    "nalesnik": ["nalesniki", "maka"],
    "placek": ["maka", "jajko"],
    # Lunch dishes
    "zup": ["bulion", "warzywa"],
    "salatk": ["salata", "warzywa"],
    "kurczak": ["kurczak", "filet z kurczaka"],
    "kotlet": ["mieso", "bulka tarta"],
    "makaron": ["makaron"],
    "ryz": ["ryz"],
    "ziemniak": ["ziemniaki"],
    "pierogi": ["pierogi", "maka"],
    "gulasz": ["wolowina", "mieso"],
    "schabowy": ["schab", "wieprzowina"],
    # Dinner dishes
    "serek": ["serek", "twarog"],
    "twarog": ["twarog"],
    "warzy": ["warzywa"],
    "salat": ["salata"],
    # Common ingredients often mentioned
    "banan": ["banan"],
    "jabłk": ["jablko"],
    "pomidor": ["pomidor"],
    "ogorек": ["ogorek"],
    "rzodkiew": ["rzodkiewka"],
    "ser": ["ser"],
    "szyn": ["szynka"],
    "wedlin": ["wedlina"],
}

# Polish stop words to filter out from description extraction
POLISH_STOP_WORDS = {
    "z", "i", "na", "w", "do", "od", "za", "po", "dla", "bez", "ze",
    "oraz", "lub", "nad", "pod", "przed", "przez", "przy", "u", "o",
}


class BielikMealPlannerAdapter(MealPlannerPort):
    """
    Meal planner adapter using existing Bielik 4.5B model.

    Uses lazy loading to defer model initialization until first use.
    The model is a singleton managed by SLMLoader.
    """

    # Meal distribution for calculating per-meal macro targets
    MEAL_DISTRIBUTION: Dict[str, float] = {
        "breakfast": 0.25,
        "second_breakfast": 0.10,
        "lunch": 0.35,
        "snack": 0.10,
        "dinner": 0.20,
    }

    def __init__(self) -> None:
        """Initialize adapter with lazy model loading."""
        self._model: Any = None
        self._embedding_service = EmbeddingService()

    def _get_model(self) -> Any:
        """
        Get the Bielik model instance (lazy loading).

        Uses SLMLoader singleton to avoid multiple model instances.

        Returns:
            Llama model instance
        """
        if self._model is None:
            from src.ai.infrastructure.nlu.slm_loader import SLMLoader

            self._model = SLMLoader.get_model()
            logger.info("BielikMealPlannerAdapter: Model loaded via SLMLoader")
        return self._model

    def _build_prompt(self, system: str, user: str) -> str:
        """
        Build prompt in Bielik instruction format.

        Uses Llama 2 style: [INST] system + user [/INST]
        Note: Removed explicit <s> as it's often added by the tokenizer/server.

        Args:
            system: System prompt with instructions
            user: User prompt with specific request

        Returns:
            Formatted prompt string
        """
        return f"[INST] {system}\n\n{user} [/INST]"

    async def generate_meal_templates(
        self,
        profile: UserProfile,
        days: int = 7
    ) -> List[List[MealTemplate]]:
        """
        Generate meal structure templates for each day.

        Uses day-by-day generation with JSON grammar for reliability.
        Each day is generated separately to avoid context window limitations.

        Args:
            profile: User profile with daily targets and preferences
            days: Number of days to generate

        Returns:
            List of days, each containing list of meal templates
        """
        model = self._get_model()
        grammar = self._get_day_template_grammar()

        all_templates: List[List[MealTemplate]] = []
        previous_descriptions: List[str] = []  # Track for variety

        for day_num in range(1, days + 1):
            logger.info(f"Generating templates for day {day_num}/{days}...")

            # Build strong context about previous days for variety
            if previous_descriptions:
                recent = previous_descriptions[-15:]  # Last 15 meal descriptions
                forbidden_list = ", ".join(recent)
                previous_context = f"\n\nZAKAZANE (juz uzyte): {forbidden_list}"
            else:
                previous_context = ""

            user_prompt = TEMPLATE_GENERATION_PROMPT_SINGLE_DAY.format(
                kcal=profile.daily_kcal,
                preferences=self._format_preferences(profile.preferences),
                previous_days_context=previous_context,
            )

            full_prompt = self._build_prompt(MEAL_PLANNER_SYSTEM_PROMPT, user_prompt)
            
            # --- LOGGING DEBUG INFO ---
            logger.info(f"Day {day_num} Generation Context:")
            logger.info(f"Diet: {profile.preferences.get('diet')}")
            logger.info(f"Allergies: {profile.preferences.get('allergies')}")
            logger.debug(f"Full Prompt to LLM:\n{full_prompt}")
            # --------------------------

            # Try with grammar first, fallback without if it fails
            day_templates = await self._generate_single_day_templates(
                model, full_prompt, grammar, profile, day_num
            )

            all_templates.append(day_templates)

            # Track descriptions for variety in next days
            for t in day_templates:
                previous_descriptions.append(t.description)

        # Post-processing: detect and fix repeated meals
        all_templates = self._deduplicate_meal_templates(all_templates, profile)

        # Filter out templates whose descriptions contain allergens
        return self._filter_templates_by_allergies(all_templates, profile)

    async def _generate_single_day_templates(
        self,
        model,
        prompt: str,
        grammar,
        profile: UserProfile,
        day_num: int,
    ) -> List[MealTemplate]:
        """
        Generate templates for a single day with retry logic.

        Tries grammar-based generation first, falls back to regular generation,
        then to default templates if all fails.

        Args:
            model: Llama model instance
            prompt: Full prompt for generation
            grammar: JSON grammar for structured output
            profile: User profile for macro calculations
            day_num: Day number (for logging)

        Returns:
            List of meal templates for the day
        """
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Try with grammar on first attempt, without on retry
                use_grammar = (attempt == 0) and (grammar is not None)

                call_kwargs = {
                    "max_tokens": MAX_TOKENS_TEMPLATES,
                    "temperature": TEMPERATURE_TEMPLATES,
                    "stop": ["</s>", "[INST]"],
                }
                if use_grammar:
                    call_kwargs["grammar"] = grammar

                response = await asyncio.to_thread(
                    model,
                    prompt,
                    **call_kwargs
                )

                response_text = response["choices"][0]["text"]
                logger.debug(f"Day {day_num} response (attempt {attempt + 1}): {response_text[:300]}...")

                if not response_text.strip():
                    raise ValueError("Empty response from LLM")

                # Parse single day response
                templates = self._parse_single_day_templates(response_text, profile, day_num)

                if templates and len(templates) >= 3:  # At least 3 valid meals
                    logger.info(f"  ✓ Day {day_num}: {len(templates)} meals generated")
                    return templates
                else:
                    raise ValueError(f"Only {len(templates)} meals parsed, need at least 3")

            except Exception as e:
                logger.warning(
                    f"Day {day_num} generation failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(f"Day {day_num}: using default templates")
                    return self._generate_default_day_templates(profile)

        return self._generate_default_day_templates(profile)

    def _get_day_template_grammar(self):
        """
        Get JSON grammar for day template generation.

        Returns:
            LlamaGrammar instance or None if not available
        """
        try:
            from llama_cpp import LlamaGrammar
            return LlamaGrammar.from_json_schema(DAY_TEMPLATE_JSON_SCHEMA)
        except ImportError:
            logger.warning("LlamaGrammar not available, generating without grammar constraints")
            return None
        except Exception as e:
            logger.warning(f"Failed to create grammar: {e}")
            return None

    def _get_meal_grammar(self):
        """
        Get JSON grammar for meal generation.

        Returns:
            LlamaGrammar instance or None if not available
        """
        try:
            from llama_cpp import LlamaGrammar
            return LlamaGrammar.from_json_schema(MEAL_JSON_SCHEMA)
        except ImportError:
            return None
        except Exception as e:
            logger.warning(f"Failed to create meal grammar: {e}")
            return None

    def _clean_description(self, description: str) -> str:
        """
        Clean meal description from LLM artifacts.
        
        Removes parentheses, comments, and meta-text.
        Example: "Kanapka (bez sera)" -> "Kanapka"
        Example: "Jajecznica - bo zdrowa" -> "Jajecznica"
        """
        if not description:
            return "Posilek"
            
        # Remove content in parentheses
        cleaned = re.sub(r'\(.*?\)', '', description)
        
        # Remove comments after - or :
        if " - " in cleaned:
            cleaned = cleaned.split(" - ")[0]
        if ": " in cleaned:
             cleaned = cleaned.split(": ")[0]
             
        # Remove common meta-phrases if they appear at start
        meta_phrases = ["zamiast", "uwaga", "zakaz", "alternatywa"]
        for phrase in meta_phrases:
            if cleaned.lower().startswith(phrase):
                cleaned = cleaned.replace(phrase, "", 1)
                
        return cleaned.strip()

    def _parse_single_day_templates(
        self,
        response: str,
        profile: UserProfile,
        day_num: int,
    ) -> List[MealTemplate]:
        """
        Parse LLM response for a single day into meal templates.

        Args:
            response: Raw LLM response
            profile: User profile for macro calculations
            day_num: Day number (for logging)

        Returns:
            List of meal templates for the day
        """
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Day {day_num}: Failed to parse JSON: {e}")
            return []

        EXPECTED_MEAL_TYPES = ["breakfast", "second_breakfast", "lunch", "snack", "dinner"]

        # Default descriptions and keywords for missing meals
        default_descriptions = {
            "breakfast": "Owsianka z owocami",
            "second_breakfast": "Jogurt z orzechami",
            "lunch": "Kurczak z warzywami i ryzem",
            "snack": "Owoce z orzechami",
            "dinner": "Kanapki z serem i warzywami",
        }
        default_keywords = {
            "breakfast": ["platki owsiane", "mleko", "banan", "jagody"],
            "second_breakfast": ["jogurt", "orzechy", "miod"],
            "lunch": ["kurczak", "ryz", "warzywa", "marchew", "brokuly"],
            "snack": ["jablko", "orzechy", "banan"],
            "dinner": ["chleb", "ser", "pomidor", "ogorek", "salata"],
        }

        templates: List[MealTemplate] = []
        seen_types: set = set()

        for meal_data in data.get("meals", []):
            meal_type = meal_data.get("type", "snack")

            # Deduplicate
            if meal_type in seen_types:
                continue
            seen_types.add(meal_type)

            ratio = self.MEAL_DISTRIBUTION.get(meal_type, 0.20)
            
            raw_desc = meal_data.get("description", default_descriptions.get(meal_type, "Posilek"))
            description = self._clean_description(raw_desc)

            # Extract keywords
            raw_keywords = meal_data.get("keywords", [])
            if isinstance(raw_keywords, list) and raw_keywords:
                keywords = [k.strip().lower() for k in raw_keywords if isinstance(k, str) and k.strip()]
            else:
                keywords = self._extract_keywords_from_description(description)

            if not keywords:
                keywords = default_keywords.get(meal_type, [])

            template = MealTemplate(
                meal_type=meal_type,
                target_kcal=int(profile.daily_kcal * ratio),
                target_protein=round(profile.daily_protein * ratio, 1),
                target_fat=round(profile.daily_fat * ratio, 1),
                target_carbs=round(profile.daily_carbs * ratio, 1),
                description=description,
                ingredient_keywords=keywords,
            )
            templates.append(template)

        # Fill missing meal types
        for mt in EXPECTED_MEAL_TYPES:
            if mt not in seen_types:
                ratio = self.MEAL_DISTRIBUTION.get(mt, 0.20)
                templates.append(MealTemplate(
                    meal_type=mt,
                    target_kcal=int(profile.daily_kcal * ratio),
                    target_protein=round(profile.daily_protein * ratio, 1),
                    target_fat=round(profile.daily_fat * ratio, 1),
                    target_carbs=round(profile.daily_carbs * ratio, 1),
                    description=default_descriptions.get(mt, "Posilek"),
                    ingredient_keywords=default_keywords.get(mt, []),
                ))
                logger.debug(f"Day {day_num}: filled missing meal type '{mt}'")

        return templates

    async def generate_meal(
        self,
        template: MealTemplate,
        profile: UserProfile,
        used_ingredients: List[str],
        available_products: List[dict]
    ) -> GeneratedMeal:
        """
        Generate a single meal with ingredients from available products.

        Uses indexed product format where LLM selects by number [1-50].
        This ensures 100% of ingredients are matched to database products.
        Uses JSON grammar for reliable structured output.

        Args:
            template: Meal template to fill with ingredients
            profile: User profile for preferences
            used_ingredients: Recently used ingredient names (for variety)
            available_products: Products from RAG search

        Returns:
            Complete meal with ingredients and calculated nutrition
        """
        model = self._get_model()
        grammar = self._get_meal_grammar()

        # Format products as indexed list (limit to context size)
        products_limited = available_products[:MAX_PRODUCTS_IN_PROMPT]
        products_text, index_map = self._format_products_indexed(products_limited)

        logger.debug(
            f"  📋 Providing {len(products_limited)} products to LLM for '{template.description}'"
        )

        # Format used ingredients (limit for context)
        used_limited = used_ingredients[-MAX_USED_INGREDIENTS_IN_PROMPT:]
        used_text = ", ".join(used_limited) if used_limited else "brak"

        user_prompt = MEAL_GENERATION_PROMPT.format(
            description=template.description,
            target_kcal=template.target_kcal,
            target_protein=template.target_protein,
            target_fat=template.target_fat,
            target_carbs=template.target_carbs,
            products=products_text,
            used=used_text,
        )

        full_prompt = self._build_prompt(MEAL_PLANNER_SYSTEM_PROMPT, user_prompt)

        logger.debug(f"Meal generation prompt length: {len(full_prompt)}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use grammar on first attempt, without on retries
                use_grammar = (attempt == 0) and (grammar is not None)

                call_kwargs = {
                    "max_tokens": MAX_TOKENS_MEAL,
                    "temperature": TEMPERATURE_MEAL + (attempt * 0.1),  # Increase temp on retry
                    "stop": ["</s>", "[INST]"],
                }
                if use_grammar:
                    call_kwargs["grammar"] = grammar

                response = await asyncio.to_thread(
                    model,
                    full_prompt,
                    **call_kwargs
                )

                response_text = response["choices"][0]["text"]
                logger.debug(f"Meal generation response (attempt {attempt+1}): {response_text[:300]}...")

                if not response_text.strip():
                    raise ValueError("Empty response from LLM")

                return self._parse_meal_indexed(response_text, template, index_map)

            except Exception as e:
                logger.warning(f"Meal generation failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error("Max retries reached, returning fallback meal")
                    return self._generate_fallback_meal(template, available_products)

        return self._generate_fallback_meal(template, available_products)

    async def optimize_plan(
        self,
        days: List[GeneratedDay],
        profile: UserProfile
    ) -> List[GeneratedDay]:
        """
        Optimize the complete plan for nutritional balance.

        Adjusts portions to better hit macro targets. This is done
        programmatically without additional LLM calls for efficiency.

        Args:
            days: Generated days to optimize
            profile: User profile with target macros

        Returns:
            Optimized list of days with adjusted portions
        """
        for day in days:
            # 1. Per-Meal Normalization
            # Check if individual meals are too far off their expected share
            for meal in day.meals:
                target_ratio = self.MEAL_DISTRIBUTION.get(meal.meal_type, 0.20)
                meal_target = profile.daily_kcal * target_ratio
                
                scale_correction = 1.0
                
                # If meal is very small (< 60% of target), boost it
                if meal.total_kcal < meal_target * 0.6:
                     # Target 75% as safe minimum
                     desired = meal_target * 0.75
                     if meal.total_kcal > 0:
                        scale_correction = desired / meal.total_kcal
                
                # If meal is very large (> 140% of target), reduce it
                elif meal.total_kcal > meal_target * 1.4:
                     # Target 125% as safe maximum
                     desired = meal_target * 1.25
                     scale_correction = desired / meal.total_kcal
                
                # Apply correction if significant
                if abs(scale_correction - 1.0) > 0.05:
                    logger.debug(
                        f"Day {day.day_number}, {meal.meal_type}: correcting imbalance "
                        f"(current {meal.total_kcal:.0f}, target {meal_target:.0f}) -> scale {scale_correction:.2f}"
                    )
                    for ing in meal.ingredients:
                        ing.amount_grams *= scale_correction
                        ing.kcal *= scale_correction
                        ing.protein *= scale_correction
                        ing.fat *= scale_correction
                        ing.carbs *= scale_correction
                    
                    meal.total_kcal *= scale_correction
                    meal.total_protein *= scale_correction
                    meal.total_fat *= scale_correction
                    meal.total_carbs *= scale_correction

            # 2. Global Scaling
            # Recalculate day total after corrections
            day_kcal = sum(m.total_kcal for m in day.meals)

            if day_kcal > 0:
                # Calculate ratio to target
                ratio = profile.daily_kcal / day_kcal

                # Only adjust if significantly off (>5% - tighter tolerance)
                if abs(ratio - 1.0) > 0.05:
                    # Limit scaling to reasonable range
                    # Relaxed lower limit to 0.5 to handle huge overshoots
                    scale = min(max(ratio, 0.5), 3.0)

                    logger.debug(
                        f"Day {day.day_number}: global scaling by {scale:.2f} "
                        f"(current {day_kcal:.0f} kcal, target {profile.daily_kcal})"
                    )

                    for meal in day.meals:
                        for ing in meal.ingredients:
                            ing.amount_grams *= scale
                            ing.kcal *= scale
                            ing.protein *= scale
                            ing.fat *= scale
                            ing.carbs *= scale

                        meal.total_kcal *= scale
                        meal.total_protein *= scale
                        meal.total_fat *= scale
                        meal.total_carbs *= scale

        return days

    def _format_products_indexed(self, products: List[dict]) -> Tuple[str, Dict[int, dict]]:
        """
        Format products as indexed list for LLM selection.

        Each product gets a unique index that the LLM will use to reference it.
        This eliminates name matching issues completely.

        Format: [1] Name | 165 kcal | B:25g T:3g W:0g

        Args:
            products: List of product dicts from RAG search

        Returns:
            Tuple of (formatted_text, index_to_product_map)
        """
        index_map: Dict[int, dict] = {}
        lines = []

        for idx, p in enumerate(products, start=1):
            index_map[idx] = p
            kcal = p.get("kcal_per_100g", 0)
            protein = p.get("protein_per_100g", 0)
            fat = p.get("fat_per_100g", 0)
            carbs = p.get("carbs_per_100g", 0)

            lines.append(
                f"[{idx}] {p['name']} | {kcal:.0f} kcal | "
                f"B:{protein:.0f}g T:{fat:.0f}g W:{carbs:.0f}g"
            )

        return "\n".join(lines), index_map

    def _format_preferences(self, preferences: dict) -> str:
        """
        Format preferences dictionary into human-readable string.

        Args:
            preferences: User preferences dict

        Returns:
            Formatted string for prompt
        """
        parts = []

        if preferences.get("diet"):
            diets = {
                "vegetarian": "WEGETARIANSKA (ZAKAZ MIESA, WEDLIN, RYB, OWOCOW MORZA)",
                "vegan": "WEGANSKA (ZAKAZ PRODUKTOW ZWIERZECYCH: MIESA, JAJ, NABIALU, MIODU)",
                "keto": "KETOGENICZNA (DUZO TLUSZCZU, BARDZO MALO WEGLOWODANOW. ZAKAZ: CUKIER, MĄKA, ZIEMNIAKI, RYŻ, MAKARON)",
                "paleo": "PALEO (ZAKAZ ZBOZ, NABIALU, PRZETWORZONEJ ZYWNOSCI, CUKRU)",
                "mediterranean": "SRODZIEMNOMORSKA (DUZO WARZYW, OLIWY, RYB, ORZECHOW. ZAKAZ PRZETWORZONEJ ZYWNOSCI)",
            }
            diet_name = diets.get(preferences['diet'], preferences['diet']).upper()
            parts.append(f"DIETA: {diet_name}")

        if preferences.get("allergies"):
            # Translate common English allergies to Polish for the LLM
            translation_map = {
                "eggs": "JAJKA",
                "egg": "JAJKA",
                "milk": "MLEKO",
                "dairy": "NABIAŁ",
                "nuts": "ORZECHY",
                "peanuts": "ORZECHY ZIEMNE",
                "fish": "RYBY",
                "seafood": "OWOCE MORZA",
                "shellfish": "OWOCE MORZA",
                "wheat": "PSZENICA (GLUTEN)",
                "gluten": "GLUTEN",
                "soy": "SOJA",
                "celery": "SELER",
                "mustard": "GORCZYCA",
            }
            
            raw_allergies = preferences['allergies']
            translated_allergies = []
            for a in raw_allergies:
                a_lower = a.lower().strip()
                translated_allergies.append(translation_map.get(a_lower, a))
                
            allergies_list = ", ".join(translated_allergies).upper()
            parts.append(f"ALERGIA NA: {allergies_list} (BEZWZGLEDNY ZAKAZ!)")

        if preferences.get("cuisine_preferences"):
            # Translate cuisine names to Polish
            cuisine_translation = {
                "polish": "POLSKA",
                "italian": "WŁOSKA",
                "mexican": "MEKSYKAŃSKA",
                "asian": "AZJATYCKA",
                "indian": "INDYJSKA",
                "american": "AMERYKAŃSKA",
                "french": "FRANCUSKA",
                "mediterranean": "ŚRÓDZIEMNOMORSKA",
                "vegetarian": "WEGETARIAŃSKA",
                "vegan": "WEGAŃSKA",
            }
            
            raw_cuisines = preferences['cuisine_preferences']
            translated_cuisines = []
            for c in raw_cuisines:
                c_lower = c.lower().strip()
                translated_cuisines.append(cuisine_translation.get(c_lower, c))
                
            parts.append(f"PREFEROWANA KUCHNIA: {', '.join(translated_cuisines).upper()}")

        if preferences.get("excluded_ingredients"):
            parts.append(f"WYKLUCZONE SKLADNIKI: {', '.join(preferences['excluded_ingredients']).upper()}")

        return "\n".join(parts) if parts else "BRAK SZCZEGOLNYCH WYMAGAN - standardowa polska kuchnia"

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from LLM response.

        Handles both code-block wrapped JSON and raw JSON.
        Attempts to clean common JSON errors and isolate the valid JSON object.
        Validates extracted JSON with json.loads() and falls back to shorter
        substrings if the initial extraction is invalid.

        Args:
            text: Raw LLM response text

        Returns:
            JSON string

        Raises:
            ValueError: If no valid JSON found
        """
        text = text.strip()

        # 1. Try code block extraction
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            candidate = match.group(1)
            candidate = self._clean_json(candidate)
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass  # Fall through to general extraction

        # 2. Find the first '{'
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found (no opening brace)")

        # 3. Brace-counting to find matching '}'
        count = 0
        end_idx = -1
        for i, char in enumerate(text[start_idx:], start=start_idx):
            if char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count == 0:
                    end_idx = i
                    break

        if end_idx == -1:
            end_idx = text.rfind('}')
            if end_idx < start_idx:
                raise ValueError("No JSON object found (no closing brace)")

        json_str = self._clean_json(text[start_idx:end_idx + 1])

        # 4. Validate with json.loads; if invalid, try shorter substrings
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass

        # Fallback: try each '}' from end to find valid JSON
        search_region = text[start_idx:]
        for i in range(len(search_region) - 1, 0, -1):
            if search_region[i] == '}':
                candidate = self._clean_json(search_region[:i + 1])
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue

        raise ValueError("No valid JSON object found in response")

    def _clean_json(self, json_str: str) -> str:
        """
        Clean common JSON errors from LLM output.

        Removes single-line comments and trailing commas before
        closing braces/brackets.

        Args:
            json_str: Raw JSON string

        Returns:
            Cleaned JSON string
        """
        json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r',(\s*[\}\]])', r'\1', json_str)
        return json_str

    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """
        Extract ingredient keywords from a meal description.

        Uses two strategies:
        1. Match dish name stems to known ingredients (e.g., "kanapki" -> ["chleb"])
        2. Extract remaining words as potential ingredients

        Args:
            description: Meal description (e.g., "Kanapki z twarogiem i rzodkiewka")

        Returns:
            List of ingredient keywords for product search
        """
        if not description:
            return []

        description_lower = description.lower()
        keywords: List[str] = []

        # Strategy 1: Map known dish stems to ingredients
        for dish_stem, ingredients in DISH_TO_INGREDIENTS.items():
            if dish_stem in description_lower:
                keywords.extend(ingredients)

        # Strategy 2: Extract remaining words (skip stop words)
        words = re.findall(r'[a-ząćęłńóśźż]+', description_lower)
        for word in words:
            # Skip short words, stop words, and already-matched dish stems
            if len(word) < 3:
                continue
            if word in POLISH_STOP_WORDS:
                continue
            # Check if word is a dish stem (not a product)
            is_dish_stem = any(dish_stem in word or word in dish_stem
                              for dish_stem in DISH_TO_INGREDIENTS.keys())
            if is_dish_stem:
                continue
            # Add as potential ingredient if not already present
            if word not in keywords and not any(word in k or k in word for k in keywords):
                keywords.append(word)

        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:5]  # Limit to 5 keywords

    def _parse_templates(
        self,
        response: str,
        profile: UserProfile,
        expected_days: int
    ) -> List[List[MealTemplate]]:
        """
        Parse LLM response into meal templates.

        Args:
            response: Raw LLM response
            profile: User profile for macro calculations
            expected_days: Expected number of days

        Returns:
            List of days with meal templates
        """
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse templates JSON: {e}")
            # Return default templates as fallback
            return self._generate_default_templates(profile, expected_days)

        EXPECTED_MEAL_TYPES = ["breakfast", "second_breakfast", "lunch", "snack", "dinner"]

        # Default descriptions with specific meal ideas (not just "Podwieczorek")
        default_descriptions = {
            "breakfast": "Owsianka z owocami",
            "second_breakfast": "Jogurt z orzechami",
            "lunch": "Kurczak z warzywami i ryzem",
            "snack": "Owoce z orzechami",
            "dinner": "Kanapki z serem i warzywami",
        }

        # Default ingredient keywords for when LLM doesn't provide meal types
        default_keywords = {
            "breakfast": ["platki owsiane", "mleko", "banan", "jagody"],
            "second_breakfast": ["jogurt", "orzechy", "miod"],
            "lunch": ["kurczak", "ryz", "warzywa", "marchew", "brokuly"],
            "snack": ["jablko", "orzechy", "banan"],
            "dinner": ["chleb", "ser", "pomidor", "ogorek", "salata"],
        }

        templates: List[List[MealTemplate]] = []

        for day_idx, day_data in enumerate(data.get("days", [])):
            day_templates: List[MealTemplate] = []
            seen_types: set = set()

            for meal_data in day_data.get("meals", []):
                meal_type = meal_data.get("type", "snack")

                # Deduplicate: skip duplicate meal types (keep first)
                if meal_type in seen_types:
                    logger.warning(
                        f"Day {day_idx + 1}: duplicate meal_type '{meal_type}' "
                        f"in LLM output, skipping"
                    )
                    continue
                seen_types.add(meal_type)

                ratio = self.MEAL_DISTRIBUTION.get(meal_type, 0.20)
                description = meal_data.get("description", f"Posilek {meal_type}")

                # Extract keywords from LLM response or fallback to extraction
                raw_keywords = meal_data.get("keywords", [])
                if isinstance(raw_keywords, list) and raw_keywords:
                    # Normalize keywords: lowercase, strip whitespace
                    keywords = [k.strip().lower() for k in raw_keywords if isinstance(k, str) and k.strip()]
                else:
                    # Fallback: extract keywords from description
                    keywords = self._extract_keywords_from_description(description)

                if keywords:
                    logger.debug(
                        f"Day {day_idx + 1}, {meal_type}: keywords = {keywords}"
                    )

                template = MealTemplate(
                    meal_type=meal_type,
                    target_kcal=int(profile.daily_kcal * ratio),
                    target_protein=round(profile.daily_protein * ratio, 1),
                    target_fat=round(profile.daily_fat * ratio, 1),
                    target_carbs=round(profile.daily_carbs * ratio, 1),
                    description=description,
                    ingredient_keywords=keywords,
                )
                day_templates.append(template)

            # Fill missing meal types with defaults (including keywords!)
            for mt in EXPECTED_MEAL_TYPES:
                if mt not in seen_types:
                    ratio = self.MEAL_DISTRIBUTION.get(mt, 0.20)
                    day_templates.append(MealTemplate(
                        meal_type=mt,
                        target_kcal=int(profile.daily_kcal * ratio),
                        target_protein=round(profile.daily_protein * ratio, 1),
                        target_fat=round(profile.daily_fat * ratio, 1),
                        target_carbs=round(profile.daily_carbs * ratio, 1),
                        description=default_descriptions.get(mt, "Posilek"),
                        ingredient_keywords=default_keywords.get(mt, []),
                    ))
                    logger.warning(
                        f"Day {day_idx + 1}: LLM didn't generate '{mt}', using default template"
                    )

            templates.append(day_templates)

        # Pad with defaults if not enough days generated
        while len(templates) < expected_days:
            templates.append(self._generate_default_day_templates(profile))

        return templates[:expected_days]

    def _generate_default_templates(
        self,
        profile: UserProfile,
        days: int
    ) -> List[List[MealTemplate]]:
        """
        Generate default templates when LLM parsing fails.

        Args:
            profile: User profile
            days: Number of days

        Returns:
            Default templates for all days
        """
        return [self._generate_default_day_templates(profile) for _ in range(days)]

    def _generate_default_day_templates(self, profile: UserProfile) -> List[MealTemplate]:
        """
        Generate default templates for a single day.

        Args:
            profile: User profile

        Returns:
            List of default meal templates
        """
        # Default descriptions with specific meal ideas
        default_descriptions = {
            "breakfast": "Owsianka z owocami",
            "second_breakfast": "Jogurt z orzechami",
            "lunch": "Kurczak z warzywami i ryzem",
            "snack": "Owoce z orzechami",
            "dinner": "Kanapki z serem i warzywami",
        }

        # Default ingredient keywords for product search
        default_keywords = {
            "breakfast": ["platki owsiane", "mleko", "banan", "jagody"],
            "second_breakfast": ["jogurt", "orzechy", "miod"],
            "lunch": ["kurczak", "ryz", "warzywa", "marchew"],
            "snack": ["jablko", "orzechy", "banan"],
            "dinner": ["chleb", "ser", "pomidor", "ogorek", "salata"],
        }

        templates = []
        for meal_type, ratio in self.MEAL_DISTRIBUTION.items():
            templates.append(MealTemplate(
                meal_type=meal_type,
                target_kcal=int(profile.daily_kcal * ratio),
                target_protein=round(profile.daily_protein * ratio, 1),
                target_fat=round(profile.daily_fat * ratio, 1),
                target_carbs=round(profile.daily_carbs * ratio, 1),
                description=default_descriptions.get(meal_type, "Posilek"),
                ingredient_keywords=default_keywords.get(meal_type, []),
            ))
        return templates

    def _deduplicate_meal_templates(
        self,
        templates: List[List[MealTemplate]],
        profile: UserProfile,
    ) -> List[List[MealTemplate]]:
        """
        Detect and replace repeated meal descriptions across all days.

        Tracks all meal descriptions and replaces duplicates with alternatives
        from a pool of varied meals.

        Args:
            templates: List of days, each with meal templates
            profile: User profile for macro calculations

        Returns:
            Templates with duplicates replaced by alternatives
        """
        # Pool of alternative meals for each type (used when duplicates found)
        alternatives = {
            "breakfast": [
                ("Jajecznica z warzywami", ["jajko", "pomidor", "cebula"]),
                ("Kanapki z serem", ["chleb", "ser", "maslo"]),
                ("Jogurt z musli", ["jogurt", "musli", "owoce"]),
                ("Kasza jaglana z owocami", ["kasza jaglana", "jablko", "cynamon"]),
                ("Omlet z warzywami", ["jajko", "papryka", "szpinak"]),
                ("Twarozek z rzodkiewka", ["twarog", "rzodkiewka", "szczypiorek"]),
            ],
            "second_breakfast": [
                ("Owoc i orzechy", ["banan", "orzechy"]),
                ("Jogurt naturalny", ["jogurt", "miod"]),
                ("Koktajl owocowy", ["mleko", "banan", "truskawki"]),
                ("Marchewka z hummusem", ["marchew", "hummus"]),
                ("Serek wiejski", ["serek wiejski", "ogorek"]),
            ],
            "lunch": [
                ("Zupa pomidorowa z ryzem", ["pomidory", "ryz", "bulion"]),
                ("Piersi z kurczaka z kaszą", ["kurczak", "kasza gryczana", "warzywa"]),
                ("Makaron z warzywami", ["makaron", "cukinia", "papryka"]),
                ("Ryba z ziemniakami", ["dorsz", "ziemniaki", "brokuly"]),
                ("Gulasz wołowy", ["wolowina", "ziemniaki", "marchew"]),
                ("Risotto z pieczarkami", ["ryz", "pieczarki", "cebula"]),
            ],
            "snack": [
                ("Jablko", ["jablko"]),
                ("Banan", ["banan"]),
                ("Orzechy wloskie", ["orzechy"]),
                ("Jogurt", ["jogurt"]),
                ("Marchewka", ["marchew"]),
            ],
            "dinner": [
                ("Salatka grecka", ["ogorek", "pomidor", "ser feta", "oliwki"]),
                ("Twarozek z ogorkiem", ["twarog", "ogorek", "rzodkiewka"]),
                ("Jajka sadzone z pieczywem", ["jajko", "chleb", "maslo"]),
                ("Zupa krem z brokułow", ["brokuly", "smietana", "bulion"]),
                ("Kanapki z szynka", ["chleb", "szynka", "salata"]),
                ("Omlet z serem", ["jajko", "ser", "szczypiorek"]),
            ],
        }

        # Track seen descriptions (normalized for comparison)
        seen_descriptions: Dict[str, int] = {}  # description -> count

        def normalize(desc: str) -> str:
            """Normalize description for comparison."""
            return desc.lower().strip()

        def is_similar(desc1: str, desc2: str) -> bool:
            """Check if two descriptions are similar."""
            n1, n2 = normalize(desc1), normalize(desc2)
            # Exact match
            if n1 == n2:
                return True
            # One contains the other
            if n1 in n2 or n2 in n1:
                return True
            # Same first 2 words (e.g., "Kurczak z warzywami" vs "Kurczak z ryzem")
            words1 = n1.split()[:2]
            words2 = n2.split()[:2]
            if words1 == words2 and len(words1) >= 2:
                return True
            return False

        # Count occurrences first
        for day_templates in templates:
            for template in day_templates:
                key = normalize(template.description)
                seen_descriptions[key] = seen_descriptions.get(key, 0) + 1

        # Track which alternatives have been used
        used_alternatives: Dict[str, int] = {}  # meal_type -> next index to use

        # Replace duplicates
        seen_once: set = set()
        replacements_made = 0

        for day_idx, day_templates in enumerate(templates):
            for i, template in enumerate(day_templates):
                key = normalize(template.description)

                # Check if this is a duplicate
                is_duplicate = False
                if key in seen_once:
                    is_duplicate = True
                else:
                    # Check for similar descriptions
                    for seen_key in seen_once:
                        if is_similar(key, seen_key):
                            is_duplicate = True
                            break

                if is_duplicate:
                    # Find an alternative
                    meal_type = template.meal_type
                    alt_list = alternatives.get(meal_type, [])
                    alt_idx = used_alternatives.get(meal_type, 0)

                    if alt_idx < len(alt_list):
                        new_desc, new_keywords = alt_list[alt_idx]
                        used_alternatives[meal_type] = alt_idx + 1

                        logger.info(
                            f"Day {day_idx + 1}: Replacing duplicate '{template.description}' "
                            f"with '{new_desc}'"
                        )

                        templates[day_idx][i] = MealTemplate(
                            meal_type=template.meal_type,
                            target_kcal=template.target_kcal,
                            target_protein=template.target_protein,
                            target_fat=template.target_fat,
                            target_carbs=template.target_carbs,
                            description=new_desc,
                            ingredient_keywords=new_keywords,
                        )
                        replacements_made += 1
                        seen_once.add(normalize(new_desc))
                    else:
                        # No more alternatives, keep the duplicate but log it
                        logger.warning(
                            f"Day {day_idx + 1}: No alternative for duplicate '{template.description}'"
                        )
                        seen_once.add(key)
                else:
                    seen_once.add(key)

        if replacements_made > 0:
            logger.info(f"Deduplication: replaced {replacements_made} duplicate meals")

        return templates

    def _filter_templates_by_allergies(
        self,
        templates: List[List[MealTemplate]],
        profile: UserProfile,
    ) -> List[List[MealTemplate]]:
        """
        Replace templates whose descriptions contain allergens with safe defaults.

        Scans each template description against allergen stems and replaces
        matching ones with generic descriptions.

        Args:
            templates: List of days, each with meal templates
            profile: User profile containing preferences with allergies

        Returns:
            Templates with allergen-containing descriptions replaced
        """
        from src.ai.infrastructure.search.pgvector_search import ALLERGEN_KEYWORD_STEMS

        user_allergies = [a.lower() for a in profile.preferences.get("allergies", []) if a]
        
        # Add implicit allergies based on diet
        diet = (profile.preferences.get("diet") or "").lower()
        if diet in ["vegetarian", "wegetarianska"]:
            user_allergies.extend(["mieso", "mięso", "kurczak", "wolowina", "wołowina", "wieprzowina", "ryba", "dorsz", "losos", "łosoś", "tunczyk", "tuńczyk", "sledz", "śledź", "kielbasa", "kiełbasa", "szynka", "boczek"])
        elif diet in ["vegan", "weganska"]:
            user_allergies.extend(["mieso", "mięso", "kurczak", "ryba", "jajka", "jajko", "mleko", "ser", "jogurt", "miod", "miód", "maslo", "masło", "smietana", "śmietana"])
        elif diet in ["keto", "ketogeniczna"]:
             user_allergies.extend(["cukier", "maka", "mąka", "ziemniaki", "ryz", "ryż", "makaron", "chleb", "bulka", "bułka", "kasza", "banan", "winogrona", "jablko", "jabłko", "gruszka", "platki", "płatki", "owsianka", "kanapka", "kanapki", "nalesniki", "naleśniki", "pierogi"])
        elif diet in ["paleo"]:
             user_allergies.extend(["nabial", "nabiał", "ser", "jogurt", "zboza", "zboża", "chleb", "makaron", "ryz", "ryż", "cukier", "przetworzona", "owsianka", "kanapka", "kanapki"])
        elif diet in ["mediterranean", "srodziemnomorska"]:
             user_allergies.extend(["przetworzona", "fast food", "chipsy", "cola", "slodycze", "słodycze", "cukier", "maka pszenna", "mąka pszenna", "bialy chleb", "biały chleb"])

        if not user_allergies:
            return templates

        # Identify which known allergens are present in the user's allergy list
        # We check if any known allergen key (e.g. "jajka") appears in the user's string (e.g. "uczulenie na jajka")
        active_stems = []
        
        # Also keep track of raw strings for direct matching in case of unknown allergies
        active_raw_allergies = list(user_allergies)

        for known_allergen, stems in ALLERGEN_KEYWORD_STEMS.items():
            # Check if this known allergen is mentioned in any of user's allergy strings
            is_active = False
            for user_allergy in user_allergies:
                if known_allergen in user_allergy:
                    is_active = True
                    break
            
            if is_active:
                active_stems.extend(stems)
        
        # Dynamic safe meal pool
        # Format: "meal_type": [ (description, keywords, [allergens_in_dish]) ]
        # The system will pick the first dish that doesn't contain user's allergies.
        
        SAFE_MEALS_POOL = {
            "breakfast": [
                ("Jajecznica z pomidorami", ["jajko", "pomidor", "szczypiorek"], ["jajko", "jaja", "jajka"]),
                ("Owsianka na wodzie z owocami", ["platki owsiane", "woda", "jablko", "banan"], ["gluten", "owsian"]),
                ("Kasza jaglana z jablkiem", ["kasza jaglana", "jablko", "cynamon"], ["gluten"]),
                ("Jajecznica z boczkiem", ["jajko", "boczek", "cebula"], ["jajko", "mieso", "wieprzowina"]), # Keto safe
            ],
            "second_breakfast": [
                ("Jogurt naturalny z orzechami", ["jogurt", "orzechy"], ["mleko", "laktoza", "nabiał", "orzechy"]),
                ("Kanapka z szynka", ["chleb", "maslo", "szynka", "pomidor"], ["gluten", "mleko", "laktoza", "nabiał", "mieso", "wieprzowina", "chleb"]), 
                ("Sałatka z awokado i jajkiem", ["awokado", "jajko", "oliwa"], ["jajko"]), # Keto/Paleo safe
                ("Salatka owocowa", ["jablko", "banan", "gruszka", "winogrona"], ["cukier"]),
            ],
            "lunch": [
                ("Makaron z sosem pomidorowym", ["makaron", "sos pomidorowy", "bazylia"], ["gluten", "jajko", "makaron"]),
                ("Kurczak z ryzem i warzywami", ["pierś z kurczaka", "ryz", "marchew", "groszek"], ["mieso", "kurczak", "ryz"]),
                ("Ryż z ciecierzycą i warzywami", ["ryz", "ciecierzyca", "papryka", "cukinia"], ["ryz"]), 
                ("Piers z kurczaka z warzywami na parze", ["pierś z kurczaka", "brokuly", "kalafior", "oliwa"], ["mieso", "kurczak"]), # Keto/Paleo safe
                ("Pieczony losos ze szpinakiem", ["losos", "szpinak", "czosnek", "cytryna"], ["ryba", "ryby"]), # Keto/Paleo/Med safe
            ],
            "snack": [
                ("Kefir z owocami", ["kefir", "truskawki"], ["mleko", "laktoza", "nabiał"]),
                ("Orzechy i owoce", ["orzechy wloskie", "jablko"], ["orzechy", "cukier"]),
                ("Słupki marchewki z hummusem", ["marchew", "hummus"], ["sezam"]), 
                ("Garsc orzechow", ["orzechy wloskie", "migdaly"], ["orzechy"]), # Keto safe
            ],
            "dinner": [
                ("Twarozek z rzodkiewka", ["twarog", "rzodkiewka", "szczypiorek"], ["mleko", "laktoza", "nabiał"]),
                ("Salatka z tunczykiem", ["tunczyk", "salata", "kukurydza", "ogorek"], ["ryby", "ryba", "mieso"]),
                ("Salatka grecka bez sera", ["pomidor", "ogorek", "oliwki", "oliwa"], []), 
                ("Satatka z grillowanym kurczakiem", ["kurczak", "salata", "pomidor", "oliwa"], ["mieso", "kurczak"]), # Keto safe
            ]
        }

        def _get_safe_meal(meal_type: str, blocked_allergens: List[str]) -> Tuple[str, List[str]]:
            options = SAFE_MEALS_POOL.get(meal_type, [])
            # Try to find first option that doesn't have any blocked allergens
            for desc, keywords, dish_allergens in options:
                is_safe = True
                for dish_allergen in dish_allergens:
                    # Check if this dish allergen is one of the user's blocked triggers
                    if dish_allergen in blocked_allergens:
                        is_safe = False
                        break
                
                # Also check against user's raw allergy strings just in case
                # e.g. if user has "uczulenie na pomidory" and dish is "Omlet z pomidorami"
                start_safe_check = is_safe
                if is_safe:
                    desc_lower = desc.lower()
                    for user_allergy in active_raw_allergies: # active_raw_allergies from outer scope
                        if user_allergy in desc_lower:
                            is_safe = False
                            break
                            
                if is_safe:
                    return desc, keywords
            
            # If nothing found (super allergic user), return the last option as best effort fallback
            # or a truly generic safe fallback
            if options:
                return options[-1][0], options[-1][1]
            return "Posilek owocowy", ["jablko", "banan"]

        for day_templates in templates:
            for i, template in enumerate(day_templates):
                desc_lower = template.description.lower()
                blocked = False
                
                # Check against active stems (derived from known allergies)
                for stem in active_stems:
                    if stem in desc_lower:
                        blocked = True
                        break
                
                # Fallback: check against raw allergy strings if not blocked yet
                if not blocked:
                    for raw_allergy in active_raw_allergies:
                        if raw_allergy in desc_lower:
                            blocked = True
                            break

                if blocked:
                    # Determine which known allergens are active for this user to pass to safe meal selector
                    # We can use active_stems, but we need high-level categories (like 'gluten')
                    # So we reconstruct a set of blocked keys.
                    blocked_keys = []
                    for k, stems in ALLERGEN_KEYWORD_STEMS.items():
                        if any(stem in active_stems for stem in stems):
                             blocked_keys.append(k)
                    
                    # Also include raw allergies
                    blocked_keys.extend(active_raw_allergies)

                    safe_desc, safe_keywords = _get_safe_meal(template.meal_type, blocked_keys)
                    
                    logger.warning(
                        f"Template '{template.description}' blocked. Replaced with safe option: '{safe_desc}'"
                    )
                    
                    day_templates[i] = MealTemplate(
                        meal_type=template.meal_type,
                        target_kcal=template.target_kcal,
                        target_protein=template.target_protein,
                        target_fat=template.target_fat,
                        target_carbs=template.target_carbs,
                        description=safe_desc,
                        ingredient_keywords=safe_keywords,
                    )

        return templates

    def _parse_meal_indexed(
        self,
        response: str,
        template: MealTemplate,
        index_map: Dict[int, dict]
    ) -> GeneratedMeal:
        """
        Parse LLM response using indexed product references.

        The LLM responds with {"idx": 1, "grams": 150} format, which we map
        directly to products via the index_map. This ensures 100% of
        ingredients are matched to database products.

        Args:
            response: Raw LLM response
            template: Original meal template
            index_map: Mapping of index -> product dict from _format_products_indexed

        Returns:
            Generated meal with ingredients (all with valid food_id)
        """
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse meal JSON: {e}")
            # Convert index_map values to list for fallback
            available_products = list(index_map.values())
            return self._generate_fallback_meal(template, available_products)

        ingredients: List[GeneratedIngredient] = []
        total_kcal = 0.0
        total_protein = 0.0
        total_fat = 0.0
        total_carbs = 0.0

        for ing_data in data.get("ingredients", []):
            # Get index (support both "idx" and "index")
            idx = ing_data.get("idx") or ing_data.get("index")
            if idx is None:
                logger.warning(f"Ingredient missing idx: {ing_data}")
                continue

            try:
                idx = int(idx)
            except (ValueError, TypeError):
                logger.warning(f"Invalid idx value: {idx}")
                continue

            # Look up product by index
            product = index_map.get(idx)
            if not product:
                logger.warning(f"  ⚠️ Invalid product index {idx}, skipping")
                continue

            # Parse grams (support "grams", "amount_grams", "amount")
            raw_grams = (
                ing_data.get("grams")
                or ing_data.get("amount_grams")
                or ing_data.get("amount")
            )
            try:
                if isinstance(raw_grams, str):
                    clean_grams = re.sub(r"[^\d.]", "", raw_grams)
                    grams = float(clean_grams) if clean_grams else 100.0
                else:
                    grams = float(raw_grams) if raw_grams is not None else 100.0
            except (ValueError, TypeError):
                grams = 100.0

            # Clamp to reasonable range
            grams = max(5.0, min(grams, 1000.0))
            
            logger.debug(f"  ✓ LLM selected [{idx}]: {product['name']} ({grams:.0f}g)")

            # Calculate nutrition from database values (not estimates!)
            factor = grams / 100.0
            kcal = product.get("kcal_per_100g", 0) * factor
            protein = product.get("protein_per_100g", 0) * factor
            fat = product.get("fat_per_100g", 0) * factor
            carbs = product.get("carbs_per_100g", 0) * factor

            # Get food_id (guaranteed to exist since product is from DB)
            food_id = product.get("id")
            if food_id and isinstance(food_id, str):
                try:
                    food_id = UUID(food_id)
                except ValueError:
                    food_id = None

            ingredient = GeneratedIngredient(
                food_id=food_id,
                name=product["name"],  # Use exact name from database
                amount_grams=round(grams, 1),
                unit_label=None,
                kcal=round(kcal, 1),
                protein=round(protein, 1),
                fat=round(fat, 1),
                carbs=round(carbs, 1),
            )
            ingredients.append(ingredient)

            total_kcal += kcal
            total_protein += protein
            total_fat += fat
            total_carbs += carbs

        # If no valid ingredients, use fallback
        if not ingredients:
            logger.warning("No valid ingredients parsed, using fallback")
            available_products = list(index_map.values())
            return self._generate_fallback_meal(template, available_products)

        return GeneratedMeal(
            meal_type=template.meal_type,
            name=data.get("name", template.description),
            description=data.get("description", ""),
            preparation_time_minutes=data.get("preparation_time", 20),
            ingredients=ingredients,
            total_kcal=round(total_kcal, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
            total_carbs=round(total_carbs, 1),
        )

    def _generate_fallback_meal(
        self,
        template: MealTemplate,
        available_products: Optional[List[dict]] = None
    ) -> GeneratedMeal:
        """
        Generate a minimal fallback meal when parsing fails.

        Args:
            template: Original meal template

        Returns:
            Basic generated meal with real ingredients from database
        """
        # If no products available, return minimal fallback
        if not available_products:
            logger.warning("No products available for fallback meal")
            return GeneratedMeal(
                meal_type=template.meal_type,
                name=template.description,
                description="Posilek wygenerowany automatycznie (brak produktow)",
                preparation_time_minutes=15,
                ingredients=[],
                total_kcal=template.target_kcal,
                total_protein=template.target_protein,
                total_fat=template.target_fat,
                total_carbs=template.target_carbs,
            )

        # Sort products by calorie content (higher first for easier portion calculation)
        sorted_products = sorted(
            available_products,
            key=lambda p: p.get("kcal_per_100g", 0),
            reverse=True
        )

        # Select top 3-4 products
        selected = sorted_products[:min(4, len(sorted_products))]

        # Calculate grams for each product to hit target kcal
        # Distribute calories roughly equally among selected products
        target_per_ingredient = template.target_kcal / len(selected)

        ingredients: List[GeneratedIngredient] = []
        total_kcal = 0.0
        total_protein = 0.0
        total_fat = 0.0
        total_carbs = 0.0

        for product in selected:
            kcal_per_100g = product.get("kcal_per_100g", 100)
            if kcal_per_100g <= 0:
                kcal_per_100g = 100  # Fallback to avoid division by zero

            # Calculate grams to hit target calories for this ingredient
            grams = (target_per_ingredient / kcal_per_100g) * 100
            # Clamp to reasonable range
            grams = max(30.0, min(grams, 300.0))

            factor = grams / 100.0
            kcal = kcal_per_100g * factor
            protein = product.get("protein_per_100g", 0) * factor
            fat = product.get("fat_per_100g", 0) * factor
            carbs = product.get("carbs_per_100g", 0) * factor

            # Get food_id
            food_id = product.get("id")
            if food_id and isinstance(food_id, str):
                try:
                    food_id = UUID(food_id)
                except ValueError:
                    food_id = None

            ingredient = GeneratedIngredient(
                food_id=food_id,
                name=product["name"],
                amount_grams=round(grams, 1),
                unit_label=None,
                kcal=round(kcal, 1),
                protein=round(protein, 1),
                fat=round(fat, 1),
                carbs=round(carbs, 1),
            )
            ingredients.append(ingredient)

            total_kcal += kcal
            total_protein += protein
            total_fat += fat
            total_carbs += carbs

        return GeneratedMeal(
            meal_type=template.meal_type,
            name=template.description,
            description="Posilek wygenerowany automatycznie",
            preparation_time_minutes=15,
            ingredients=ingredients,
            total_kcal=round(total_kcal, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
            total_carbs=round(total_carbs, 1),
        )
