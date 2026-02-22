import { z } from "zod";
import { MealType } from "@/types/food";

export const manualFoodSchema = z.object({
  name: z.string().min(1, "Name is required"),
  calories: z.coerce.number().min(0).default(0),
  protein: z.coerce.number().min(0).default(0),
  fat: z.coerce.number().min(0).default(0),
  carbs: z.coerce.number().min(0).default(0),
  weight: z.coerce.number().min(1).default(100),
  mealType: z.enum(MealType),
  glycemic_index: z.coerce.number().optional().nullable(),
});

export type ManualFoodFormValues = z.infer<typeof manualFoodSchema>;
