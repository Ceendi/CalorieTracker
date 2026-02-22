import { z } from "zod";

/**
 * Zod schemas for meal plan API response validation.
 * Based on backend schemas in meal_planning/api/schemas.py
 */

export const PlanPreferencesSchema = z.object({
  diet: z.string().nullable().optional(),
  allergies: z.array(z.string()).default([]),
  cuisine_preferences: z.array(z.string()).default(["polish"]),
  excluded_ingredients: z.array(z.string()).default([]),
  max_preparation_time: z.number().nullable().optional(),
});

export const GeneratePlanRequestSchema = z.object({
  name: z.string().nullable().optional(),
  start_date: z.string(), // YYYY-MM-DD format
  days: z.number().min(1).max(14).default(7),
  preferences: PlanPreferencesSchema.optional(),
});

export const GeneratePlanResponseSchema = z.object({
  task_id: z.string(),
  message: z.string(),
});

export const GenerationStatusResponseSchema = z.object({
  status: z.enum(["started", "generating", "completed", "error", "unknown"]),
  progress: z.number().optional(),
  message: z.string().optional(),
  plan_id: z.string().optional(),
  error: z.string().optional(),
  day: z.number().optional(),
});

export const DailyTargetsResponseSchema = z.object({
  kcal: z.number(),
  protein: z.number(),
  fat: z.number(),
  carbs: z.number(),
});

export const IngredientSchema = z.object({
  id: z.uuid(),
  food_id: z.string().uuid().nullable().optional(),
  name: z.string(),
  amount_grams: z.number(),
  unit_label: z.string().nullable().optional(),
  kcal: z.number().nullable().optional(),
  protein: z.number().nullable().optional(),
  fat: z.number().nullable().optional(),
  carbs: z.number().nullable().optional(),
  gi_per_100g: z.number().nullable().optional(),
});

export const MealSchema = z.object({
  id: z.uuid(),
  meal_type: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  preparation_time_minutes: z.number().nullable().optional(),
  ingredients: z.array(IngredientSchema).default([]),
  total_kcal: z.number().nullable().optional(),
  total_protein: z.number().nullable().optional(),
  total_fat: z.number().nullable().optional(),
  total_carbs: z.number().nullable().optional(),
});

export const DaySchema = z.object({
  id: z.uuid(),
  day_number: z.number(),
  date: z.string().nullable().optional(), // Uses alias from backend
  meals: z.array(MealSchema).default([]),
});

export const DailyTargetsSchema = z.object({
  kcal: z.number().optional(),
  calories: z.number().optional(),
  protein: z.number(),
  fat: z.number(),
  carbs: z.number(),
});

export const MealPlanSchema = z.object({
  id: z.uuid(),
  name: z.string().nullable().optional(),
  start_date: z.string(),
  end_date: z.string(),
  status: z.string(),
  preferences: z.record(z.string(), z.unknown()).nullable().optional(),
  daily_targets: DailyTargetsSchema.nullable().optional(),
  days: z.array(DaySchema).default([]),
});

export const MealPlanSummarySchema = z.object({
  id: z.uuid(),
  name: z.string().nullable().optional(),
  start_date: z.string(),
  end_date: z.string(),
  status: z.string(),
});

export const MealPlanListResponseSchema = z.object({
  plans: z.array(MealPlanSummarySchema),
});

export type PlanPreferences = z.infer<typeof PlanPreferencesSchema>;
export type GeneratePlanRequest = z.infer<typeof GeneratePlanRequestSchema>;
export type GeneratePlanResponse = z.infer<typeof GeneratePlanResponseSchema>;
export type GenerationStatusResponse = z.infer<
  typeof GenerationStatusResponseSchema
>;
export type DailyTargets = z.infer<typeof DailyTargetsResponseSchema>;
export type Ingredient = z.infer<typeof IngredientSchema>;
export type Meal = z.infer<typeof MealSchema>;
export type Day = z.infer<typeof DaySchema>;
export type MealPlan = z.infer<typeof MealPlanSchema>;
export type MealPlanSummary = z.infer<typeof MealPlanSummarySchema>;
export type MealPlanListResponse = z.infer<typeof MealPlanListResponseSchema>;
