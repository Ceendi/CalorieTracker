/**
 * Nutrition values per 100g
 * Note: Backend uses kcal_per_100g, frontend uses calories_per_100g
 * Mapping is done in tracking.service.ts and food.service.ts
 */
export interface Nutrition {
  calories_per_100g: number; // Backend: kcal_per_100g
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
}

/**
 * Unit conversion info for a food product
 * Maps to backend FoodUnitModel / UnitInfoSchema
 */
export interface UnitInfo {
  unit: string;    // UnitType enum value
  grams: number;   // How many grams equals 1 unit
  label: string;   // Display label (UnitLabel enum)
}

/**
 * Food product from catalogue
 * Maps to backend FoodOutSchema
 */
export interface FoodProduct {
  id: string | null;
  name: string;
  barcode?: string;
  category?: string;
  default_unit?: string;
  nutrition: Nutrition;
  owner_id?: string;
  source?: string; // 'public' | 'fineli' | 'openfoodfacts' | 'user'
  brand?: string;
  units?: UnitInfo[];
}

export interface Food extends FoodProduct {}

/**
 * Meal type enum - matches backend MealType
 */
export enum MealType {
  BREAKFAST = "breakfast",
  LUNCH = "lunch",
  DINNER = "dinner",
  SNACK = "snack"
}

/**
 * Request DTO for creating a single meal entry
 * Maps to backend MealEntryCreate
 */
export interface CreateEntryDto {
  date: string; // YYYY-MM-DD
  meal_type: MealType;
  product_id: string; // UUID
  amount_grams: number;
  unit_label?: string;
  unit_grams?: number;
  unit_quantity?: number;
}

/**
 * Single item in bulk meal creation
 * Maps to backend MealEntryBase
 */
export interface BulkMealItem {
  product_id: string;
  amount_grams: number;
  unit_label?: string;
  unit_grams?: number;
  unit_quantity?: number;
}

/**
 * Request DTO for bulk meal creation (voice input)
 * Maps to backend MealBulkCreate
 */
export interface CreateBulkEntryDto {
  date: string;
  meal_type: MealType;
  items: BulkMealItem[];
}

/**
 * Request DTO for creating custom food
 * Maps to backend CreateCustomFoodIn
 */
export interface CreateFoodDto {
  name: string;
  barcode?: string;
  nutrition: Nutrition;
}

/**
 * Meal entry in daily log
 * Maps to backend MealEntryRead
 * Note: product is constructed on frontend from product_id + product_name
 */
export interface MealEntry {
  id: string;
  daily_log_id?: string;
  user_id?: string;
  product: FoodProduct; // Constructed on frontend
  product_id: string;
  date: string;
  meal_type: MealType;
  amount_grams: number;
  // Computed values from backend
  calories: number;  // Backend: computed_kcal
  protein: number;   // Backend: computed_protein
  fat: number;       // Backend: computed_fat
  carbs: number;     // Backend: computed_carbs
  // Unit info
  unit_label?: string;
  unit_grams?: number;
  unit_quantity?: number;
}

/**
 * Daily log with all meal entries
 * Maps to backend DailyLogRead
 */
export interface DailyLog {
  id: string;
  date: string;
  entries: MealEntry[];
  total_kcal: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
}

