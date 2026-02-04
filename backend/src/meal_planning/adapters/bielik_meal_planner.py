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
    TEMPLATE_GENERATION_PROMPT,
    MEAL_GENERATION_PROMPT,
    MAX_TOKENS_TEMPLATES,
    MAX_TOKENS_MEAL,
    TEMPERATURE,
    MAX_PRODUCTS_IN_PROMPT,
    MAX_USED_INGREDIENTS_IN_PROMPT,
)
from src.ai.infrastructure.embedding.embedding_service import EmbeddingService
import numpy as np


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

        Args:
            profile: User profile with daily targets and preferences
            days: Number of days to generate

        Returns:
            List of days, each containing list of meal templates
        """
        model = self._get_model()

        # Build the user prompt
        user_prompt = TEMPLATE_GENERATION_PROMPT.format(
            days=days,
            kcal=profile.daily_kcal,
            breakfast_kcal=int(profile.daily_kcal * 0.25),
            snack1_kcal=int(profile.daily_kcal * 0.10),
            lunch_kcal=int(profile.daily_kcal * 0.35),
            snack2_kcal=int(profile.daily_kcal * 0.10),
            dinner_kcal=int(profile.daily_kcal * 0.20),
            preferences=self._format_preferences(profile.preferences),
        )

        full_prompt = self._build_prompt(MEAL_PLANNER_SYSTEM_PROMPT, user_prompt)

        logger.debug(f"Template generation prompt length: {len(full_prompt)}")

        # Call model in thread pool (llama-cpp is sync)
        response = await asyncio.to_thread(
            model,
            full_prompt,
            max_tokens=MAX_TOKENS_TEMPLATES,
            temperature=TEMPERATURE,
            stop=["</s>", "[INST]"],
        )

        response_text = response["choices"][0]["text"]
        logger.debug(f"Template generation response: {response_text[:500]}...")

        templates = self._parse_templates(response_text, profile, days)

        # Filter out templates whose descriptions contain allergens
        return self._filter_templates_by_allergies(templates, profile)

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

        Args:
            template: Meal template to fill with ingredients
            profile: User profile for preferences
            used_ingredients: Recently used ingredient names (for variety)
            available_products: Products from RAG search

        Returns:
            Complete meal with ingredients and calculated nutrition
        """
        model = self._get_model()

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
                # Call model in thread pool
                response = await asyncio.to_thread(
                    model,
                    full_prompt,
                    max_tokens=MAX_TOKENS_MEAL,
                    temperature=TEMPERATURE + (attempt * 0.1),  # Increase temp slightly on retry
                    stop=["</s>", "[INST]"],
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
            day_kcal = day.total_kcal

            if day_kcal > 0:
                # Calculate ratio to target
                ratio = profile.daily_kcal / day_kcal

                # Only adjust if significantly off (>10%)
                if abs(ratio - 1.0) > 0.1:
                    # Limit scaling to reasonable range
                    # Increased upper limit to 3.0 to handle cases where initial plan is much lower
                    scale = min(max(ratio, 0.85), 3.0)

                    logger.debug(
                        f"Day {day.day_number}: scaling by {scale:.2f} "
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
                "vegetarian": "wegetarianska",
                "vegan": "weganska",
                "keto": "ketogeniczna",
            }
            parts.append(f"dieta {diets.get(preferences['diet'], preferences['diet'])}")

        if preferences.get("allergies"):
            parts.append(f"bez: {', '.join(preferences['allergies'])}")

        if preferences.get("cuisine_preferences"):
            parts.append(f"kuchnia: {', '.join(preferences['cuisine_preferences'])}")

        if preferences.get("excluded_ingredients"):
            parts.append(f"wykluczone: {', '.join(preferences['excluded_ingredients'])}")

        return ", ".join(parts) if parts else "standardowa polska kuchnia"

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

        default_descriptions = {
            "breakfast": "Sniadanie",
            "second_breakfast": "Drugie sniadanie",
            "lunch": "Obiad",
            "snack": "Podwieczorek",
            "dinner": "Kolacja",
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

                template = MealTemplate(
                    meal_type=meal_type,
                    target_kcal=int(profile.daily_kcal * ratio),
                    target_protein=round(profile.daily_protein * ratio, 1),
                    target_fat=round(profile.daily_fat * ratio, 1),
                    target_carbs=round(profile.daily_carbs * ratio, 1),
                    description=meal_data.get("description", f"Posilek {meal_type}"),
                )
                day_templates.append(template)

            # Fill missing meal types with defaults
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
                    ))
                    logger.debug(f"Day {day_idx + 1}: added missing meal type '{mt}'")

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
        default_descriptions = {
            "breakfast": "Sniadanie",
            "second_breakfast": "Drugie sniadanie",
            "lunch": "Obiad",
            "snack": "Podwieczorek",
            "dinner": "Kolacja",
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
            ))
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

        allergies = [a.lower() for a in profile.preferences.get("allergies", [])]
        if not allergies:
            return templates

        default_descriptions = {
            "breakfast": "Sniadanie",
            "second_breakfast": "Drugie sniadanie",
            "lunch": "Obiad",
            "snack": "Podwieczorek",
            "dinner": "Kolacja",
        }

        for day_templates in templates:
            for i, template in enumerate(day_templates):
                desc_lower = template.description.lower()
                blocked = False
                for allergen in allergies:
                    stems = ALLERGEN_KEYWORD_STEMS.get(allergen)
                    if stems:
                        if any(stem in desc_lower for stem in stems):
                            blocked = True
                            break
                    else:
                        if allergen in desc_lower:
                            blocked = True
                            break

                if blocked:
                    safe_desc = default_descriptions.get(
                        template.meal_type, "Posilek"
                    )
                    logger.warning(
                        f"Template '{template.description}' contains allergen, "
                        f"replacing with '{safe_desc}'"
                    )
                    day_templates[i] = MealTemplate(
                        meal_type=template.meal_type,
                        target_kcal=template.target_kcal,
                        target_protein=template.target_protein,
                        target_fat=template.target_fat,
                        target_carbs=template.target_carbs,
                        description=safe_desc,
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
