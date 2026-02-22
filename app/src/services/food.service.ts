import { apiClient } from './api.client';
import { FoodProduct, CreateFoodDto } from '@/types/food';
import {
  FoodProductResponseSchema,
  FoodSearchResponseSchema,
  FoodProductResponse
} from '@/schemas/api';

/**
 * Map API food response to frontend FoodProduct type
 */
function mapFoodProduct(apiFood: FoodProductResponse): FoodProduct {
  return {
    id: apiFood.id,
    name: apiFood.name,
    barcode: apiFood.barcode ?? undefined,
    category: apiFood.category ?? undefined,
    default_unit: apiFood.default_unit ?? undefined,
    nutrition: {
      calories_per_100g: apiFood.nutrition.kcal_per_100g,
      protein_per_100g: apiFood.nutrition.protein_per_100g,
      fat_per_100g: apiFood.nutrition.fat_per_100g,
      carbs_per_100g: apiFood.nutrition.carbs_per_100g,
    },
    owner_id: apiFood.owner_id ?? undefined,
    source: apiFood.source ?? undefined,
    brand: apiFood.brand ?? undefined,
    units: apiFood.units,
    glycemic_index: apiFood.glycemic_index ?? undefined,
  };
}

/**
 * Ensures a food product exists in the database.
 * Creates it if it doesn't exist, handles conflicts by fetching existing.
 * @returns Product ID (UUID)
 */
export async function ensureFoodProduct(food: CreateFoodDto): Promise<string> {
  try {
    const created = await foodService.createFood(food);
    if (!created.id) throw new Error('Created food has no ID');
    return created.id;
  } catch (error) {
    // If creation failed and we have a barcode, try to fetch existing
    if (food.barcode) {
      try {
        const existing = await foodService.getFoodByBarcode(food.barcode);
        if (existing?.id) return existing.id;
      } catch {
        // Barcode lookup failed, rethrow original error
      }
    }
    throw error;
  }
}

export const foodService = {
  async searchFoods(query: string, external: boolean = false): Promise<FoodProduct[]> {
    const response = await apiClient.get(`/api/v1/foods/search`, {
      params: { q: query, external },
    });
    const validated = FoodSearchResponseSchema.parse(response.data);
    return validated.map(mapFoodProduct);
  },

  async getFoodByBarcode(barcode: string): Promise<FoodProduct> {
    const response = await apiClient.get(`/api/v1/foods/barcode/${barcode}`);
    const validated = FoodProductResponseSchema.parse(response.data);
    return mapFoodProduct(validated);
  },

  async createFood(food: CreateFoodDto): Promise<FoodProduct> {
    const payload = {
      ...food,
      nutrition: {
        kcal_per_100g: food.nutrition.calories_per_100g,
        protein_per_100g: food.nutrition.protein_per_100g,
        fat_per_100g: food.nutrition.fat_per_100g,
        carbs_per_100g: food.nutrition.carbs_per_100g,
      },
      glycemic_index: food.glycemic_index,
    };
    const response = await apiClient.post(`/api/v1/foods/custom`, payload);
    const validated = FoodProductResponseSchema.parse(response.data);
    return mapFoodProduct(validated);
  },

  async getFoodById(id: string): Promise<FoodProduct> {
    const response = await apiClient.get(`/api/v1/foods/${id}`);
    const validated = FoodProductResponseSchema.parse(response.data);
    return mapFoodProduct(validated);
  },
};
