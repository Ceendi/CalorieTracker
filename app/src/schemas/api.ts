import { z } from "zod";

/**
 * Zod schemas for API response validation
 * Ensures type safety at runtime when receiving data from backend
 */

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string().default("bearer"),
});

export const UserResponseSchema = z.object({
  id: z.uuid(),
  email: z.email(),
  is_active: z.boolean().optional().default(true),
  is_verified: z.boolean().optional().default(false),
  is_onboarded: z.boolean().optional().default(false),
  weight: z.number().nullable().optional(),
  height: z.number().nullable().optional(),
  age: z.number().nullable().optional(),
  gender: z.string().nullable().optional(),
  activity_level: z.string().nullable().optional(),
  goal: z.string().nullable().optional(),
});

export const NutritionSchema = z.object({
  kcal_per_100g: z.number().default(0),
  protein_per_100g: z.number().default(0),
  fat_per_100g: z.number().default(0),
  carbs_per_100g: z.number().default(0),
});

export const UnitInfoSchema = z.object({
  unit: z.string(),
  grams: z.number(),
  label: z.string(),
});

export const FoodProductResponseSchema = z.object({
  id: z.uuid().nullable(),
  name: z.string(),
  barcode: z.string().nullable().optional(),
  category: z.string().nullable().optional(),
  default_unit: z.string().nullable().optional(),
  nutrition: NutritionSchema,
  owner_id: z.uuid().nullable().optional(),
  source: z.string().nullable().optional(),
  brand: z.string().nullable().optional(),
  units: z.array(UnitInfoSchema).optional().default([]),
  glycemic_index: z.number().nullable().optional(),
});

export const FoodSearchResponseSchema = z.array(FoodProductResponseSchema);

export const MealEntryResponseSchema = z.object({
  id: z.uuid(),
  daily_log_id: z.uuid(),
  product_id: z.uuid(),
  product_name: z.string().default("Unknown"),
  amount_grams: z.number(),
  meal_type: z.string(),
  kcal_per_100g: z.number().default(0),
  protein_per_100g: z.number().default(0),
  fat_per_100g: z.number().default(0),
  carbs_per_100g: z.number().default(0),
  computed_kcal: z.number().default(0),
  computed_protein: z.number().default(0),
  computed_fat: z.number().default(0),
  computed_carbs: z.number().default(0),
  unit_label: z.string().nullable().optional(),
  unit_grams: z.number().nullable().optional(),
  unit_quantity: z.number().nullable().optional(),
  gi_per_100g: z.number().nullable().optional(),
});

export const DailyLogResponseSchema = z.object({
  id: z.uuid(),
  date: z.string(),
  user_id: z.uuid().optional(),
  entries: z.array(MealEntryResponseSchema).default([]),
  total_kcal: z.number().default(0),
  total_protein: z.number().default(0),
  total_fat: z.number().default(0),
  total_carbs: z.number().default(0),
});

export const DailyLogHistoryResponseSchema = z.array(DailyLogResponseSchema);

export const ProcessedFoodItemSchema = z.object({
  product_id: z.uuid().nullable(),
  name: z.string(),
  brand: z.string().nullable().optional(),
  quantity_grams: z.number(),
  quantity_unit_value: z.number(),
  unit_matched: z.string(),
  kcal: z.number(),
  protein: z.number(),
  fat: z.number(),
  carbs: z.number(),
  kcal_per_100g: z.number(),
  protein_per_100g: z.number(),
  fat_per_100g: z.number(),
  carbs_per_100g: z.number(),
  confidence: z.number().optional(),
  status: z.enum(["matched", "not_found", "needs_confirmation"]).optional(),
  units: z.array(UnitInfoSchema).optional(),
  glycemic_index: z.number().nullable().optional(),
});

export const VoiceProcessResponseSchema = z.object({
  transcription: z.string(),
  meal_type: z.string(),
  items: z.array(ProcessedFoodItemSchema),
  processing_time_ms: z.number().optional(),
});

export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type UserResponse = z.infer<typeof UserResponseSchema>;
export type FoodProductResponse = z.infer<typeof FoodProductResponseSchema>;
export type MealEntryResponse = z.infer<typeof MealEntryResponseSchema>;
export type DailyLogResponse = z.infer<typeof DailyLogResponseSchema>;
export type VoiceProcessResponse = z.infer<typeof VoiceProcessResponseSchema>;
