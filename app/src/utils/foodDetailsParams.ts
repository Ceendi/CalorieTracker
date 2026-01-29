/**
 * Raw params from expo-router
 */
import { FoodProduct, MealType, UnitInfo } from '@/types/food';
import { FoodDetailsRawParams, FoodDetailsIntent, FoodDetailsMode } from '@/types/navigation';

export { FoodDetailsRawParams, FoodDetailsIntent, FoodDetailsMode };

/**
 * Parse raw expo-router params into a normalized FoodDetailsIntent
 */
export function parseFoodDetailsParams(params: FoodDetailsRawParams): FoodDetailsIntent {
  // Determine mode
  let mode: FoodDetailsMode = 'new';
  if (params.barcode) {
    mode = 'barcode';
  } else if (params.entryId) {
    mode = 'edit';
  }

  // Parse food from JSON if provided
  let food: FoodProduct | undefined;
  if (params.item) {
    try {
      food = JSON.parse(params.item) as FoodProduct;
    } catch (e) {
      console.error('Failed to parse food item from params:', e);
    }
  }

  // Parse initial unit
  let unit: UnitInfo | null = null;
  if (params.initialUnitLabel && params.initialUnitGrams) {
    unit = {
      label: params.initialUnitLabel,
      grams: parseFloat(params.initialUnitGrams),
      unit: params.initialUnitLabel,
    };
  }

  // Parse meal type
  let mealType: MealType | undefined;
  if (params.initialMealType && Object.values(MealType).includes(params.initialMealType as MealType)) {
    mealType = params.initialMealType as MealType;
  }

  return {
    mode,
    barcode: params.barcode,
    food,
    entryId: params.entryId,
    date: params.date,
    initialValues: {
      amount: params.initialUnitQuantity
        ? parseFloat(params.initialUnitQuantity)
        : params.initialAmount
          ? parseFloat(params.initialAmount)
          : 100,
      mealType,
      unit,
      unitQuantity: params.initialUnitQuantity ? parseFloat(params.initialUnitQuantity) : undefined,
    },
  };
}

/**
 * Serialize a FoodProduct for passing via router params
 */
export function serializeFoodForParams(food: FoodProduct): string {
  return JSON.stringify(food);
}
