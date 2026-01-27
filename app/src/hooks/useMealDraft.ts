import { useState, useEffect, useMemo, useCallback } from 'react';
import { Keyboard } from 'react-native';
import {
  MealDraft,
  MealDraftItem,
  foodProductToMealDraftItem,
  createEmptyMealDraft,
} from '@/types/meal-draft';
import { FoodProduct, MealType, UnitInfo } from '@/types/food';
import { ProcessedMeal, ProcessedFoodItem } from '@/services/ai.service';
import { formatDateForApi } from '@/utils/date';

interface UseMealDraftProps {
  initialMeal?: MealDraft | ProcessedMeal | null;
  mealType?: MealType;
  t: (key: string) => string;
}

interface UseMealDraftResult {
  draft: MealDraft | null;
  totals: { kcal: number; protein: number; fat: number; carbs: number };

  // Item management
  addItem: (product: FoodProduct, quantity?: number) => void;
  removeItem: (index: number) => void;
  updateItemQuantity: (index: number, quantity: number, unit?: UnitInfo | null) => void;

  // Meal management
  setMealType: (type: MealType | string) => void;
  cycleMealType: () => void;
  getMealTypeLabel: (type: string) => string;

  // State
  isEmpty: boolean;
  itemCount: number;
}

/**
 * Convert ProcessedMeal to MealDraft
 */
function processedMealToMealDraft(meal: ProcessedMeal): MealDraft {
  const date = formatDateForApi();

  // Guard against division by zero
  const safeGrams = (grams: number) => Math.max(grams || 100, 1);

  return {
    meal_type: meal.meal_type,
    items: meal.items.map((item): MealDraftItem => {
      const quantity = safeGrams(item.quantity_grams);
      return {
        product_id: item.product_id ? String(item.product_id) : null,
        name: item.name,
        brand: item.brand,
        quantity_grams: item.quantity_grams,
        quantity_unit_value: item.quantity_unit_value,
        unit_matched: item.unit_matched,
        kcal: item.kcal,
        protein: item.protein,
        fat: item.fat,
        carbs: item.carbs,
        kcal_per_100g: (item.kcal / quantity) * 100,
        protein_per_100g: (item.protein / quantity) * 100,
        fat_per_100g: (item.fat / quantity) * 100,
        carbs_per_100g: (item.carbs / quantity) * 100,
        confidence: item.confidence,
        status: item.status,
        units: item.units,
        source: 'voice',
      };
    }),
    date,
    raw_transcription: meal.raw_transcription,
    source: 'voice',
  };
}

/**
 * Check if object is ProcessedMeal (duck typing)
 */
function isProcessedMeal(obj: any): obj is ProcessedMeal {
  return obj && 'raw_transcription' in obj && 'processing_time_ms' in obj;
}

export function useMealDraft({
  initialMeal,
  mealType,
  t,
}: UseMealDraftProps): UseMealDraftResult {
  const [draft, setDraft] = useState<MealDraft | null>(null);

  // Initialize draft from initial data
  useEffect(() => {
    if (initialMeal) {
      if (isProcessedMeal(initialMeal)) {
        setDraft(processedMealToMealDraft(initialMeal));
      } else {
        setDraft(JSON.parse(JSON.stringify(initialMeal)));
      }
    } else if (mealType) {
      setDraft(createEmptyMealDraft(mealType));
    }
  }, [initialMeal, mealType]);

  // Calculate totals
  const totals = useMemo(() => {
    if (!draft?.items?.length) {
      return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    }
    return draft.items.reduce(
      (acc, item) => ({
        kcal: acc.kcal + item.kcal,
        protein: acc.protein + item.protein,
        fat: acc.fat + item.fat,
        carbs: acc.carbs + item.carbs,
      }),
      { kcal: 0, protein: 0, fat: 0, carbs: 0 }
    );
  }, [draft]);

  // Add new item from FoodProduct
  const addItem = useCallback((product: FoodProduct, quantity: number = 100) => {
    if (!draft) return;
    const newItem = foodProductToMealDraftItem(product, quantity);
    setDraft({
      ...draft,
      items: [...draft.items, newItem],
    });
    Keyboard.dismiss();
  }, [draft]);

  // Remove item by index
  const removeItem = useCallback((index: number) => {
    if (!draft) return;
    setDraft({
      ...draft,
      items: draft.items.filter((_, i) => i !== index),
    });
  }, [draft]);

  // Update item quantity and unit
  const updateItemQuantity = useCallback((
    index: number,
    quantity: number,
    unit?: UnitInfo | null
  ) => {
    if (!draft) return;

    const updatedItems = [...draft.items];
    const item = { ...updatedItems[index] };

    // Calculate new grams
    const gramsPerUnit = unit ? unit.grams : 1;
    const newGrams = quantity * gramsPerUnit;

    // Update unit info
    item.unit_matched = unit ? unit.label : 'g';
    item.quantity_unit_value = quantity;
    item.quantity_grams = newGrams;

    // Recalculate macros based on per-100g values
    const ratio = newGrams / 100;
    item.kcal = Math.round(item.kcal_per_100g * ratio);
    item.protein = item.protein_per_100g * ratio;
    item.fat = item.fat_per_100g * ratio;
    item.carbs = item.carbs_per_100g * ratio;

    updatedItems[index] = item;
    setDraft({ ...draft, items: updatedItems });
  }, [draft]);

  // Set meal type
  const setMealType = useCallback((type: MealType | string) => {
    if (!draft) return;
    setDraft({ ...draft, meal_type: type });
  }, [draft]);

  // Cycle through meal types
  const cycleMealType = useCallback(() => {
    if (!draft) return;
    const types = ['breakfast', 'lunch', 'dinner', 'snack'];
    const currentIdx = types.indexOf(draft.meal_type as string);
    const nextIdx = currentIdx === -1 ? 0 : (currentIdx + 1) % types.length;
    setDraft({ ...draft, meal_type: types[nextIdx] });
  }, [draft]);

  // Get translated meal type label
  const getMealTypeLabel = useCallback((type: string): string => {
    const labels: Record<string, string> = {
      'breakfast': t('meals.breakfast'),
      'second_breakfast': t('meals.second_breakfast') || t('meals.snack'),
      'lunch': t('meals.lunch'),
      'tea': t('meals.tea') || t('meals.snack'),
      'dinner': t('meals.dinner'),
      'snack': t('meals.snack'),
      // Polish variants
      'śniadanie': t('meals.breakfast'),
      'drugie_śniadanie': t('meals.snack'),
      'obiad': t('meals.lunch'),
      'podwieczorek': t('meals.snack'),
      'kolacja': t('meals.dinner'),
      'przekąska': t('meals.snack'),
    };
    return labels[type] || type;
  }, [t]);

  return {
    draft,
    totals,
    addItem,
    removeItem,
    updateItemQuantity,
    setMealType,
    cycleMealType,
    getMealTypeLabel,
    isEmpty: !draft?.items?.length,
    itemCount: draft?.items?.length || 0,
  };
}
