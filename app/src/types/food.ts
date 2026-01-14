export interface Nutrition {
  calories_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
}

export interface FoodProduct {
  id: string | null;
  name: string;
  barcode?: string;
  nutrition: Nutrition;
  owner_id?: string;
  source?: string;
  brand?: string;
}

export interface Food extends FoodProduct {}

export enum MealType {
  BREAKFAST = "breakfast",
  LUNCH = "lunch",
  DINNER = "dinner",
  SNACK = "snack"
}

export interface CreateEntryDto {
  date: string; // YYYY-MM-DD
  meal_type: MealType;
  product_id: string; // UUID
  amount_grams: number;
}

export interface CreateFoodDto {
  name: string;
  barcode?: string;
  nutrition: Nutrition;
}

export interface MealEntry {
  id: string; // UUID
  user_id: string; // UUID
  product: FoodProduct; 
  product_id: string; // UUID
  date: string;
  meal_type: MealType;
  amount_grams: number;
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
}

export interface DailyLog {
  id: string; // UUID
  date: string; // Date
  entries: MealEntry[];
  total_kcal: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
}

