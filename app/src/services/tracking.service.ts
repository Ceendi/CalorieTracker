import { apiClient } from './api.client';
import { CreateEntryDto, DailyLog, CreateBulkEntryDto, MealType } from '@/types/food';
import {
  DailyLogResponseSchema,
  DailyLogHistoryResponseSchema,
  DailyLogResponse,
  MealEntryResponse
} from '@/schemas/api';

export const trackingService = {
  async logEntry(entry: CreateEntryDto): Promise<DailyLog> {
    const response = await apiClient.post('/api/v1/tracking/entries', entry);
    const validated = DailyLogResponseSchema.parse(response.data);
    return mapLog(validated);
  },

  async logEntriesBulk(bulkData: CreateBulkEntryDto): Promise<DailyLog> {
    const response = await apiClient.post('/api/v1/tracking/bulk-entries', bulkData);
    const validated = DailyLogResponseSchema.parse(response.data);
    return mapLog(validated);
  },

  async getDailyLog(date: string): Promise<DailyLog> {
    const response = await apiClient.get(`/api/v1/tracking/daily/${date}`);
    const validated = DailyLogResponseSchema.parse(response.data);
    return mapLog(validated);
  },

  async deleteEntry(entryId: string): Promise<void> {
    await apiClient.delete(`/api/v1/tracking/entries/${entryId}`);
  },

  async updateEntry(entryId: string, updates: { amount_grams?: number; meal_type?: string }): Promise<void> {
    await apiClient.patch(`/api/v1/tracking/entries/${entryId}`, updates);
  },

  async getHistory(startDate: string, endDate: string): Promise<DailyLog[]> {
    const response = await apiClient.get('/api/v1/tracking/history', {
      params: { start_date: startDate, end_date: endDate }
    });
    const validated = DailyLogHistoryResponseSchema.parse(response.data);
    return validated.map(mapLog);
  }
};

function mapLog(apiLog: DailyLogResponse): DailyLog {
  return {
    id: apiLog.id,
    date: apiLog.date,
    total_kcal: apiLog.total_kcal,
    total_protein: apiLog.total_protein,
    total_fat: apiLog.total_fat,
    total_carbs: apiLog.total_carbs,
    entries: apiLog.entries.map((e: MealEntryResponse) => ({
      id: e.id,
      daily_log_id: e.daily_log_id,
      product_id: e.product_id,
      date: apiLog.date,
      meal_type: e.meal_type as MealType,
      amount_grams: e.amount_grams,
      product: {
        id: e.product_id || null,
        name: e.product_name,
        nutrition: {
          calories_per_100g: e.kcal_per_100g,
          protein_per_100g: e.protein_per_100g,
          fat_per_100g: e.fat_per_100g,
          carbs_per_100g: e.carbs_per_100g,
        },
        glycemic_index: e.gi_per_100g ?? undefined,
      },
      calories: e.computed_kcal,
      protein: e.computed_protein,
      fat: e.computed_fat,
      carbs: e.computed_carbs,
      unit_label: e.unit_label ?? undefined,
      unit_grams: e.unit_grams ?? undefined,
      unit_quantity: e.unit_quantity ?? undefined,
      gi_per_100g: e.gi_per_100g ?? undefined,
    }))
  };
}
