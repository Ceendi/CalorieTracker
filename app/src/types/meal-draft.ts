/**
 * Universal Meal Draft types for the MealConfirmationModal
 * Can be created from: Voice input, Manual search, or Existing entries
 */

import { MealType, FoodProduct, MealEntry, UnitInfo } from './food';
import { formatDateForApi } from '@/utils/date';

/**
 * Single item in a meal draft
 * Unified type that can represent:
 * - ProcessedFoodItem (from voice)
 * - FoodProduct (from search)
 * - MealEntry (from existing entry)
 */
export interface MealDraftItem {
  // Identification
  product_id: string | null;
  name: string;
  brand?: string;

  // Quantity
  quantity_grams: number;
  quantity_unit_value: number;
  unit_matched: string; // 'g' | unit label

  // Macros (computed based on quantity)
  kcal: number;
  protein: number;
  fat: number;
  carbs: number;

  // Per 100g values (for recalculation)
  kcal_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;

  // Metadata
  confidence?: number;
  status?: 'matched' | 'not_found' | 'needs_confirmation';
  units?: UnitInfo[];
  source?: 'voice' | 'search' | 'existing';

  // For existing entries (edit mode)
  entry_id?: string;
}

/**
 * Complete meal draft for confirmation
 */
export interface MealDraft {
  meal_type: MealType | string;
  items: MealDraftItem[];
  date: string; // YYYY-MM-DD
  raw_transcription?: string; // Only for voice input
  source: 'voice' | 'manual' | 'edit';
}

/**
 * Convert FoodProduct to MealDraftItem
 */
export function foodProductToMealDraftItem(
  product: FoodProduct,
  quantity: number = 100
): MealDraftItem {
  const ratio = quantity / 100;
  return {
    product_id: product.id,
    name: product.name,
    brand: product.brand,
    quantity_grams: quantity,
    quantity_unit_value: quantity,
    unit_matched: 'g',
    kcal: Math.round(product.nutrition.calories_per_100g * ratio),
    protein: product.nutrition.protein_per_100g * ratio,
    fat: product.nutrition.fat_per_100g * ratio,
    carbs: product.nutrition.carbs_per_100g * ratio,
    kcal_per_100g: product.nutrition.calories_per_100g,
    protein_per_100g: product.nutrition.protein_per_100g,
    fat_per_100g: product.nutrition.fat_per_100g,
    carbs_per_100g: product.nutrition.carbs_per_100g,
    confidence: 1.0,
    status: 'matched',
    units: product.units,
    source: 'search',
  };
}

/**
 * Convert MealEntry to MealDraftItem (for editing)
 */
export function mealEntryToMealDraftItem(entry: MealEntry): MealDraftItem {
  return {
    product_id: entry.product_id,
    name: entry.product?.name || 'Unknown',
    brand: entry.product?.brand,
    quantity_grams: entry.amount_grams,
    quantity_unit_value: entry.unit_quantity || entry.amount_grams,
    unit_matched: entry.unit_label || 'g',
    kcal: entry.calories,
    protein: entry.protein,
    fat: entry.fat,
    carbs: entry.carbs,
    kcal_per_100g: entry.product?.nutrition?.calories_per_100g || 0,
    protein_per_100g: entry.product?.nutrition?.protein_per_100g || 0,
    fat_per_100g: entry.product?.nutrition?.fat_per_100g || 0,
    carbs_per_100g: entry.product?.nutrition?.carbs_per_100g || 0,
    confidence: 1.0,
    status: 'matched',
    units: entry.product?.units,
    source: 'existing',
    entry_id: entry.id,
  };
}

/**
 * Create empty MealDraft for manual adding
 */
export function createEmptyMealDraft(mealType?: MealType): MealDraft {
  const date = formatDateForApi();

  // Auto-detect meal type based on time
  let autoMealType: MealType = mealType || MealType.SNACK;
  if (!mealType) {
    const hour = new Date().getHours();
    if (hour < 10) autoMealType = MealType.BREAKFAST;
    else if (hour < 14) autoMealType = MealType.LUNCH;
    else if (hour < 18) autoMealType = MealType.DINNER;
    else autoMealType = MealType.SNACK;
  }

  return {
    meal_type: autoMealType,
    items: [],
    date,
    source: 'manual',
  };
}

/**
 * Create MealDraft from existing entries (for bulk edit)
 */
export function createMealDraftFromEntries(
  entries: MealEntry[],
  mealType: MealType,
  date: string
): MealDraft {
  return {
    meal_type: mealType,
    items: entries.map(mealEntryToMealDraftItem),
    date,
    source: 'edit',
  };
}
