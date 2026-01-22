import { apiClient } from './api.client';
import { FoodProduct, CreateFoodDto, Food } from '@/types/food';

export const foodService = {
  async searchFoods(query: string): Promise<Food[]> {
    const response = await apiClient.get<Food[]>(`/api/v1/foods/search`, {
      params: { q: query },
    });
    return response.data;
  },

  async getFoodByBarcode(barcode: string): Promise<FoodProduct> {
    const response = await apiClient.get<FoodProduct>(`/api/v1/foods/barcode/${barcode}`);
    return response.data;
  },

  async createFood(food: CreateFoodDto): Promise<FoodProduct> {
    const response = await apiClient.post<FoodProduct>(`/api/v1/foods/custom`, food);
    return response.data;
  },

  async getFoodById(id: string): Promise<FoodProduct> {
    const response = await apiClient.get<FoodProduct>(`/api/v1/foods/${id}`);
    return response.data;
  },
};
