import { FoodProduct, MealType, UnitInfo } from './food';

/**
 * Raw params from expo-router for Food Details screen
 */
export interface FoodDetailsRawParams {
  entryId?: string;
  initialAmount?: string;
  initialMealType?: string;
  initialUnitLabel?: string;
  initialUnitGrams?: string;
  initialUnitQuantity?: string;
  barcode?: string;
  item?: string;
  date?: string;
}

/**
 * Intent types for the food details screen
 */
export type FoodDetailsMode = 'new' | 'edit' | 'barcode';

/**
 * Parsed and normalized params for food details
 */
export interface FoodDetailsIntent {
  mode: FoodDetailsMode;
  barcode?: string;
  food?: FoodProduct;
  entryId?: string;
  date?: string;
  initialValues: {
    amount: number;
    mealType?: MealType;
    unit?: UnitInfo | null;
    unitQuantity?: number;
  };
}
