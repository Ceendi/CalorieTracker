"""
Service layer for meal planning module.

Contains business logic for meal plan generation and management,
including BMR/CPM calculations and macro targets.
"""
from dataclasses import dataclass, asdict, field
from datetime import date
from typing import Any, Callable, Awaitable, Dict, List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
import json

from src.meal_planning.application.ports import MealPlanRepositoryPort, FoodSearchPort
from src.meal_planning.domain.entities import (
    UserProfile,
    PlanPreferences,
    GeneratedPlan,
    GeneratedDay,
    GeneratedMeal,
    GeneratedIngredient,
    ProgressCallback,
)
from src.meal_planning.domain.ports import MealPlannerPort


@dataclass
class UserData:
    """
    User data required for meal plan calculations.

    This is a simple data transfer object that contains the user
    attributes needed to calculate BMR, CPM, and daily targets.
    Compatible with the User model from the users module.

    Attributes:
        id: User ID
        weight: Weight in kilograms
        height: Height in centimeters
        age: Age in years
        gender: Gender ('male' or 'female')
        activity_level: Activity level (sedentary, light, moderate, active, very_active)
        goal: Fitness goal (lose, maintain, gain)
    """
    id: UUID
    weight: float
    height: float
    age: int
    gender: str
    activity_level: str
    goal: str


class MealPlanService:
    """
    Service for meal plan generation and management.

    Handles BMR/CPM calculations, daily target generation,
    and coordinates between repository and meal planner.
    """

    MEAL_DISTRIBUTION = {
        "breakfast": 0.25,
        "second_breakfast": 0.10,
        "lunch": 0.35,
        "snack": 0.10,
        "dinner": 0.20,
    }

    # Default macro ratios (Jarosz 2020 – Normy żywienia dla populacji Polski)
    DEFAULT_PROTEIN_RATIO = 0.20  # 20% calories from protein
    DEFAULT_FAT_RATIO = 0.30      # 30% calories from fat
    DEFAULT_CARBS_RATIO = 0.50   # 50% calories from carbs

    # Activity level multipliers (PAL - Physical Activity Level)
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.4,
        "light": 1.55,
        "moderate": 1.70,
        "active": 1.85,
        "very_active": 2.0,
    }

    GOAL_ADJUSTMENTS = {
        "lose": 0.8,      # 20% calorie deficit
        "maintain": 1.0,   # No adjustment
        "gain": 1.15,      # 15% calorie surplus
    }

    def __init__(
        self,
        repository: MealPlanRepositoryPort,
        planner: Optional[MealPlannerPort] = None,
        food_search: Optional[FoodSearchPort] = None,
        session: Optional[AsyncSession] = None,
    ):
        """
        Initialize the meal plan service.

        Args:
            repository: Repository port for meal plan persistence
            planner: Optional meal planner port for generation (injected later)
            food_search: Optional food search port for RAG-based ingredient selection
                        (uses PgVectorSearchService for pgvector-based hybrid search)
            session: Database session for food search queries (required for PgVectorSearchService)
        """
        self._repo = repository
        self._planner = planner
        self._food_search = food_search
        self._session = session

    def calculate_daily_targets(
        self,
        user: UserData,
        preferences: PlanPreferences
    ) -> dict:
        """
        Calculate daily macro targets based on user profile.

        Uses Mifflin-St Jeor equation for BMR calculation,
        then applies activity level and goal adjustments.

        Args:
            user: User data with physical attributes
            preferences: Plan preferences (currently unused, for future customization)

        Returns:
            Dict with keys: kcal, protein, fat, carbs
        """
        bmr = self._calculate_bmr(user)
        cpm = bmr * self._get_activity_multiplier(user.activity_level)

        goal_factor = self.GOAL_ADJUSTMENTS.get(user.goal, 1.0)
        daily_kcal = int(cpm * goal_factor)

        # Calculate macros using default ratios
        # Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
        return {
            "kcal": daily_kcal,
            "protein": round(daily_kcal * self.DEFAULT_PROTEIN_RATIO / 4, 1),
            "fat": round(daily_kcal * self.DEFAULT_FAT_RATIO / 9, 1),
            "carbs": round(daily_kcal * self.DEFAULT_CARBS_RATIO / 4, 1),
        }

    def build_user_profile(
        self,
        user: UserData,
        preferences: PlanPreferences
    ) -> UserProfile:
        """
        Build a UserProfile for the meal planner.

        Combines calculated targets with user preferences
        into a profile suitable for meal plan generation.

        Args:
            user: User data with physical attributes
            preferences: Plan preferences

        Returns:
            UserProfile entity for the planner
        """
        targets = self.calculate_daily_targets(user, preferences)

        return UserProfile(
            user_id=user.id,
            daily_kcal=targets["kcal"],
            daily_protein=targets["protein"],
            daily_fat=targets["fat"],
            daily_carbs=targets["carbs"],
            preferences={
                "diet": preferences.diet,
                "allergies": preferences.allergies,
                "cuisine_preferences": preferences.cuisine_preferences,
                "excluded_ingredients": preferences.excluded_ingredients,
            }
        )

    def _calculate_bmr(self, user: UserData) -> float:
        """
        Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Formula:
        - Male: BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        - Female: BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

        Args:
            user: User data with weight, height, age, and gender

        Returns:
            BMR in kcal/day
        """
        base = 10 * user.weight + 6.25 * user.height - 5 * user.age
        if user.gender == "male":
            return base + 5
        else:
            return base - 161

    def _get_activity_multiplier(self, level: str) -> float:
        """
        Get the Physical Activity Level (PAL) multiplier.

        Args:
            level: Activity level string

        Returns:
            PAL multiplier (defaults to 'moderate' if unknown)
        """
        return self.ACTIVITY_MULTIPLIERS.get(level, 1.55)

    # Repository pass-through methods with authorization checks

    async def save_plan(
        self,
        user_id: UUID,
        plan: GeneratedPlan,
        name: str,
        start_date: date
    ) -> UUID:
        """
        Save a generated plan for a user.

        Args:
            user_id: Owner of the plan
            plan: Generated plan to save
            name: Name for the plan
            start_date: Start date of the plan

        Returns:
            UUID of the created plan
        """
        plan_id = await self._repo.create_plan(user_id, plan, name, start_date)
        await self._repo.commit()
        return plan_id

    async def get_plan(
        self,
        plan_id: UUID,
        user_id: UUID
    ) -> Optional[Any]:
        """
        Get a meal plan by ID with authorization check.

        Args:
            plan_id: ID of the plan
            user_id: ID of the requesting user

        Returns:
            Meal plan if found and user is authorized, None otherwise
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            return plan
        return None

    async def list_plans(
        self,
        user_id: UUID,
        status: Optional[str] = None
    ) -> List[Any]:
        """
        List all meal plans for a user.

        Args:
            user_id: Owner of the plans
            status: Optional status filter

        Returns:
            List of meal plans
        """
        return await self._repo.list_plans(user_id, status)

    async def delete_plan(
        self,
        plan_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a meal plan with authorization check.

        Args:
            plan_id: ID of the plan to delete
            user_id: ID of the requesting user

        Returns:
            True if deleted, False if not found or unauthorized
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            result = await self._repo.delete_plan(plan_id)
            await self._repo.commit()
            return result
        return False

    async def update_plan_status(
        self,
        plan_id: UUID,
        user_id: UUID,
        status: str
    ) -> bool:
        """
        Update the status of a meal plan with authorization check.

        Args:
            plan_id: ID of the plan
            user_id: ID of the requesting user
            status: New status value

        Returns:
            True if updated, False if not found or unauthorized
        """
        plan = await self._repo.get_plan(plan_id)
        if plan and plan.user_id == user_id:
            result = await self._repo.update_status(plan_id, status)
            await self._repo.commit()
            return result
        return False

    async def generate_plan(
        self,
        user: UserData,
        preferences: PlanPreferences,
        start_date: date,
        days: int = 7,
        progress_callback: Optional[ProgressCallback] = None
    ) -> GeneratedPlan:
        """
        Generate a complete meal plan using the LLM planner.

        This orchestrates the full generation flow:
        1. Build user profile with calculated targets
        2. Generate meal templates (structure) from LLM
        3. For each meal: search products (RAG) and generate with ingredients
        4. Optimize the complete plan

        Args:
            user: User data for target calculation
            preferences: Generation preferences (diet, allergies, etc.)
            start_date: Start date of the plan
            days: Number of days to generate (1-14)
            progress_callback: Optional async callback for progress updates

        Returns:
            Complete generated meal plan

        Raises:
            RuntimeError: If meal planner is not configured
        """
        if not self._planner:
            raise RuntimeError("Meal planner not configured")

        profile = self.build_user_profile(user, preferences)
        logger.info(
            f"Generating {days}-day plan for user {user.id}, "
            f"target: {profile.daily_kcal} kcal"
        )

        if progress_callback:
            await progress_callback({
                "stage": "profile",
                "progress": 5,
                "message": "Obliczono cele dzienne"
            })

        logger.debug("Generating meal templates...")
        templates = await self._planner.generate_meal_templates(profile, days)
        logger.debug(f"Generated templates for {len(templates)} days")

        if progress_callback:
            await progress_callback({
                "stage": "templates",
                "progress": 15,
                "message": "Wygenerowano struktury posilkow"
            })

        generated_days: List[GeneratedDay] = []
        used_ingredients: List[str] = []

        total_meals = sum(len(day_templates) for day_templates in templates)
        meals_done = 0

        for day_idx, day_templates in enumerate(templates):
            day_meals = []

            for template in day_templates:
                # Search for relevant products (RAG)
                products = await self._search_products_for_meal(template, preferences)

                logger.debug(
                    f"  Generating meal with {len(products)} available products..."
                )
                meal = await self._planner.generate_meal(
                    template=template,
                    profile=profile,
                    used_ingredients=used_ingredients,
                    available_products=products
                )
                
                logger.info(
                    f"✅ Generated '{meal.name}' with {len(meal.ingredients)} ingredients: "
                    f"{', '.join([ing.name for ing in meal.ingredients])}"
                )

                # Enrich ingredients that weren't found in initial search
                enrich_prefs = {
                    "allergies": preferences.allergies,
                    "diet": preferences.diet,
                    "excluded_ingredients": preferences.excluded_ingredients,
                }
                meal = await self._enrich_meal_ingredients(meal, enrich_prefs)

                day_meals.append(meal)

                # Track used ingredients for variety
                for ing in meal.ingredients:
                    if ing.name not in used_ingredients:
                        used_ingredients.append(ing.name)

                meals_done += 1

                if progress_callback:
                    progress = 15 + int((meals_done / total_meals) * 70)
                    await progress_callback({
                        "stage": "generating",
                        "day": day_idx + 1,
                        "meal": template.meal_type,
                        "progress": progress,
                        "message": f"Dzien {day_idx + 1}: {template.description}"
                    })

            # Defense-in-depth: deduplicate by meal_type (keep first occurrence)
            seen_types: set = set()
            deduped_meals = []
            for m in day_meals:
                if m.meal_type not in seen_types:
                    seen_types.add(m.meal_type)
                    deduped_meals.append(m)
                else:
                    logger.warning(
                        f"Day {day_idx + 1}: duplicate meal_type '{m.meal_type}' removed"
                    )
            day_meals = deduped_meals

            generated_days.append(GeneratedDay(
                day_number=day_idx + 1,
                meals=day_meals
            ))

            logger.debug(
                f"Day {day_idx + 1}: {len(day_meals)} meals, "
                f"{generated_days[-1].total_kcal:.0f} kcal"
            )

        if progress_callback:
            await progress_callback({
                "stage": "optimizing",
                "progress": 90,
                "message": "Optymalizacja planu"
            })

        optimized = await self._planner.optimize_plan(generated_days, profile)

        preferences_dict = {
            "diet": preferences.diet,
            "allergies": preferences.allergies,
            "cuisine_preferences": preferences.cuisine_preferences,
            "excluded_ingredients": preferences.excluded_ingredients,
            "max_preparation_time": preferences.max_preparation_time,
        }

        generated_plan = GeneratedPlan(
            days=optimized,
            preferences_applied=preferences_dict,
            generation_metadata={
                "daily_targets": {
                    "kcal": profile.daily_kcal,
                    "protein": profile.daily_protein,
                    "fat": profile.daily_fat,
                    "carbs": profile.daily_carbs,
                },
                "days_generated": days,
                "start_date": str(start_date),
            }
        )

        validation = self.validate_plan_quality(
            generated_plan, profile.daily_kcal, preferences=preferences_dict
        )
        generated_plan.generation_metadata["quality_validation"] = validation

        logger.info(
            f"Plan quality: {validation['food_id_percentage']:.1f}% ingredients matched, "
            f"{len(validation['empty_meals'])} empty meals, "
            f"{len(validation['calorie_deviation_days'])} days with calorie deviation, "
            f"{len(validation['allergen_violations'])} allergen violations"
        )

        try:
            plan_dict = asdict(generated_plan)
            logger.info(
                f"Generated Plan JSON:\n"
                f"{json.dumps(plan_dict, indent=2, default=str, ensure_ascii=False)}"
            )
        except Exception as e:
            logger.error(f"Failed to log plan JSON: {e}")

        if progress_callback:
            await progress_callback({
                "stage": "complete",
                "progress": 100,
                "message": "Plan gotowy"
            })

        return generated_plan

    async def _search_products_for_meal(
        self,
        template,
        preferences: PlanPreferences,
        limit: int = 15
    ) -> List[dict]:
        """
        Search for relevant products for a meal template using pgvector hybrid search.

        If the template has ingredient_keywords, searches for each keyword separately
        and merges results. Otherwise falls back to description-based search.

        Args:
            template: Meal template with description, meal_type, and ingredient_keywords
            preferences: User preferences for filtering (allergies, diet, exclusions)
            limit: Maximum products to return

        Returns:
            List of product dicts suitable for the meal, including nutrition data
        """
        if not self._food_search:
            logger.warning("Food search not configured, returning empty products")
            return []

        if not self._session:
            logger.warning("Database session not provided, returning empty products")
            return []

        preferences_dict = {
            "allergies": preferences.allergies,
            "diet": preferences.diet,
            "excluded_ingredients": preferences.excluded_ingredients,
        }

        keywords = getattr(template, 'ingredient_keywords', [])
        if keywords:
            # Use keyword-based search for better ingredient matching
            products = await self._search_products_by_keywords(
                keywords=keywords,
                meal_type=template.meal_type,
                preferences=preferences_dict,
                limit=limit,
            )
            logger.info(
                f"🔍 Keyword search for '{template.meal_type}' with {len(keywords)} keywords: "
                f"Found {len(products)} unique products"
            )
        else:
            # Fallback to description-based search
            products = await self._food_search.search_for_meal_planning(
                session=self._session,
                meal_type=template.meal_type,
                preferences=preferences_dict,
                limit=limit,
                meal_description=template.description,
            )
            logger.info(
                f"🔍 Description search for '{template.meal_type}' ({template.description}): "
                f"Found {len(products)} products"
            )

        if products:
            product_names = [p.get('name', 'Unknown') for p in products[:10]]
            logger.debug(
                f"  Top products: {', '.join(product_names)}"
                f"{' ...' if len(products) > 10 else ''}"
            )
        else:
            logger.warning(f"  ⚠️ No products found for {template.meal_type}!")

        return products

    async def _search_products_by_keywords(
        self,
        keywords: List[str],
        meal_type: str,
        preferences: Dict[str, Any],
        limit: int = 15,
    ) -> List[dict]:
        """
        Search for products using individual ingredient keywords.

        Searches for each keyword separately and merges results,
        ensuring better ingredient matching than searching for the full description.

        Args:
            keywords: List of ingredient keywords (e.g., ["chleb", "twarog", "rzodkiewka"])
            meal_type: Type of meal (for logging)
            preferences: Dietary preferences for filtering
            limit: Maximum total products to return

        Returns:
            List of unique product dicts sorted by score
        """
        if not keywords:
            return []

        all_products: Dict[str, dict] = {}  # Keyed by product ID for deduplication
        products_per_keyword = max(5, limit // len(keywords))

        for keyword in keywords:
            logger.debug(f"  Searching for keyword: '{keyword}'")

            results = await self._food_search.search_for_meal_planning(
                session=self._session,
                meal_type=meal_type,
                preferences=preferences,
                limit=products_per_keyword,
                meal_description=keyword,  # Use keyword as the search query
            )

            for product in results:
                product_id = str(product.get("id", ""))
                if product_id and product_id not in all_products:
                    all_products[product_id] = product
                    logger.debug(f"    Found: {product.get('name', 'Unknown')}")

        sorted_products = sorted(
            all_products.values(),
            key=lambda p: p.get("score", 0),
            reverse=True
        )

        return sorted_products[:limit]

    async def _enrich_meal_ingredients(
        self,
        meal: GeneratedMeal,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> GeneratedMeal:
        """
        Enrich meal ingredients by searching for products that weren't found.

        When LLM generates ingredients not in the initial meal-type search,
        we do a second pass search for each missing ingredient.

        Args:
            meal: Generated meal with potentially unmatched ingredients
            preferences: Optional dietary preferences for allergen filtering

        Returns:
            Meal with enriched ingredients (food_id and accurate nutrition)
        """
        if not self._food_search or not self._session:
            return meal

        enriched_ingredients = []
        recalc_needed = False

        for ing in meal.ingredients:
            if ing.food_id is not None:
                enriched_ingredients.append(ing)
                continue

            product = await self._food_search.find_product_by_name(
                session=self._session,
                name=ing.name,
                preferences=preferences,
            )

            if product:
                # Recalculate nutrition with actual product data
                factor = ing.amount_grams / 100.0
                food_id = UUID(product["id"]) if isinstance(product["id"], str) else product["id"]

                enriched_ing = GeneratedIngredient(
                    food_id=food_id,
                    name=product["name"],  # Use DB name for consistency
                    amount_grams=ing.amount_grams,
                    unit_label=ing.unit_label,
                    kcal=round(product.get("kcal_per_100g", 0) * factor, 1),
                    protein=round(product.get("protein_per_100g", 0) * factor, 1),
                    fat=round(product.get("fat_per_100g", 0) * factor, 1),
                    carbs=round(product.get("carbs_per_100g", 0) * factor, 1),
                )
                enriched_ingredients.append(enriched_ing)
                recalc_needed = True
                logger.info(f"  🔄 Enriched: '{ing.name}' → '{product['name']}' (ID: {food_id})")
            else:
                # Still not found, keep original with estimates
                enriched_ingredients.append(ing)
                logger.warning(f"  ⚠️ Ingredient not found in DB: '{ing.name}' (using estimates)")

        if not recalc_needed:
            return meal

        total_kcal = sum(i.kcal for i in enriched_ingredients)
        total_protein = sum(i.protein for i in enriched_ingredients)
        total_fat = sum(i.fat for i in enriched_ingredients)
        total_carbs = sum(i.carbs for i in enriched_ingredients)

        return GeneratedMeal(
            meal_type=meal.meal_type,
            name=meal.name,
            description=meal.description,
            preparation_time_minutes=meal.preparation_time_minutes,
            ingredients=enriched_ingredients,
            total_kcal=round(total_kcal, 1),
            total_protein=round(total_protein, 1),
            total_fat=round(total_fat, 1),
            total_carbs=round(total_carbs, 1),
        )

    def validate_plan_quality(
        self,
        plan: GeneratedPlan,
        daily_target_kcal: int,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate the quality of a generated meal plan.

        Checks:
        - Percentage of ingredients with valid food_id (should be 100%)
        - Daily calorie deviation from target (should be 80-120%)
        - Empty meals (meals with no ingredients)
        - Allergen violations (ingredients matching declared allergies)

        Args:
            plan: Generated plan to validate
            daily_target_kcal: Target daily calories
            preferences: Optional preferences dict with allergies list

        Returns:
            Dict with validation results:
            - food_id_percentage: float (0-100)
            - calorie_deviation_days: List of day numbers with deviation outside 80-120%
            - empty_meals: List of (day_number, meal_type) tuples
            - allergen_violations: List of (day_number, meal_type, ingredient_name, allergen)
            - issues: List of human-readable issue strings
            - is_valid: bool (True if no critical issues)
        """
        from src.ai.infrastructure.search.pgvector_search import (
            ALLERGEN_KEYWORD_STEMS,
        )

        total_ingredients = 0
        ingredients_with_food_id = 0
        calorie_deviation_days: List[int] = []
        empty_meals: List[tuple] = []
        allergen_violations: List[tuple] = []
        issues: List[str] = []

        # Build allergen stems for scanning
        allergies = []
        if preferences:
            allergies = [a.lower() for a in preferences.get("allergies", [])]

        for day in plan.days:
            day_kcal = day.total_kcal

            # Check calorie deviation (80-120% of target)
            if daily_target_kcal > 0:
                deviation = day_kcal / daily_target_kcal
                if deviation < 0.8 or deviation > 1.2:
                    calorie_deviation_days.append(day.day_number)
                    issues.append(
                        f"Dzien {day.day_number}: {day_kcal:.0f} kcal "
                        f"({deviation*100:.0f}% celu {daily_target_kcal} kcal)"
                    )

            for meal in day.meals:
                if not meal.ingredients:
                    empty_meals.append((day.day_number, meal.meal_type))
                    issues.append(
                        f"Dzien {day.day_number}, {meal.meal_type}: brak skladnikow"
                    )

                for ing in meal.ingredients:
                    total_ingredients += 1
                    if ing.food_id is not None:
                        ingredients_with_food_id += 1
                    else:
                        issues.append(
                            f"Dzien {day.day_number}, {meal.meal_type}: "
                            f"'{ing.name}' bez food_id"
                        )

                    if allergies:
                        name_lower = ing.name.lower()
                        for allergen in allergies:
                            stems = ALLERGEN_KEYWORD_STEMS.get(allergen)
                            matched = False
                            if stems:
                                matched = any(s in name_lower for s in stems)
                            else:
                                matched = allergen in name_lower
                            if matched:
                                allergen_violations.append(
                                    (day.day_number, meal.meal_type, ing.name, allergen)
                                )
                                issues.append(
                                    f"ALERGEN! Dzien {day.day_number}, {meal.meal_type}: "
                                    f"'{ing.name}' zawiera alergen '{allergen}'"
                                )

        food_id_percentage = 0.0
        if total_ingredients > 0:
            food_id_percentage = (ingredients_with_food_id / total_ingredients) * 100

        is_valid = (
            food_id_percentage >= 90.0  # At least 90% matched
            and len(empty_meals) == 0  # No empty meals
            and len(calorie_deviation_days) <= len(plan.days) // 2  # Max half days off
            and len(allergen_violations) == 0  # No allergen violations
        )

        return {
            "food_id_percentage": round(food_id_percentage, 1),
            "calorie_deviation_days": calorie_deviation_days,
            "empty_meals": empty_meals,
            "allergen_violations": allergen_violations,
            "issues": issues,
            "is_valid": is_valid,
            "total_ingredients": total_ingredients,
            "ingredients_with_food_id": ingredients_with_food_id,
        }
