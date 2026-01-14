import { apiClient } from './api.client';
import { CreateEntryDto, DailyLog, MealEntry } from '@/types/food';

export const trackingService = {
  async logEntry(entry: CreateEntryDto): Promise<DailyLog> {
    const response = await apiClient.post('/api/v1/tracking/entries', entry);
    return response.data;
  },

  async getDailyLog(date: string): Promise<DailyLog> {
    const response = await apiClient.get<any>(`/api/v1/tracking/daily/${date}`);
    return mapLog(response.data);
  },

  async deleteEntry(entryId: string): Promise<void> {
    await apiClient.delete(`/api/v1/tracking/entries/${entryId}`);
  },

  async updateEntry(entryId: string, updates: { amount_grams?: number; meal_type?: string }): Promise<void> {
    await apiClient.patch(`/api/v1/tracking/entries/${entryId}`, updates);
  },

  async getHistory(startDate: string, endDate: string): Promise<DailyLog[]> {
    const response = await apiClient.get<any[]>('/api/v1/tracking/history', {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data.map(mapLog);
  }
};

function mapLog(apiLog: any): DailyLog {
  return {
    ...apiLog,
    entries: (apiLog.entries || []).map((e: any) => ({
      ...e,
      product: {
        id: null,
        name: e.product_name || 'Unknown',
        nutrition: {
             calories_per_100g: 0,
             protein_per_100g: 0,
             fat_per_100g: 0,
             carbs_per_100g: 0
        }
      },
      calories: e.computed_kcal,
      protein: e.computed_protein,
      fat: e.computed_fat,
      carbs: e.computed_carbs
    }))
  };
}
