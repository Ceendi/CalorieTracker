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
      calories_per_100g: apiFood.kcal_per_100g,
      protein_per_100g: apiFood.protein_per_100g,
      fat_per_100g: apiFood.fat_per_100g,
      carbs_per_100g: apiFood.carbs_per_100g,
    },
    owner_id: apiFood.owner_id ?? undefined,
    source: apiFood.source ?? undefined,
    brand: apiFood.brand ?? undefined,
    units: apiFood.units,
  };
}

export const foodService = {
  async searchFoods(query: string): Promise<FoodProduct[]> {
    const response = await apiClient.get(`/api/v1/foods/search`, {
      params: { q: query },
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
    const response = await apiClient.post(`/api/v1/foods/custom`, food);
    const validated = FoodProductResponseSchema.parse(response.data);
    return mapFoodProduct(validated);
  },

  async getFoodById(id: string): Promise<FoodProduct> {
    const response = await apiClient.get(`/api/v1/foods/${id}`);
    const validated = FoodProductResponseSchema.parse(response.data);
    return mapFoodProduct(validated);
  },
};
