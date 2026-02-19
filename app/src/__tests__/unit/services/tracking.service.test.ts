import { trackingService } from '../../../services/tracking.service';
import { apiClient } from '../../../services/api.client';

jest.mock('../../../services/api.client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  },
}));

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;
const mockDelete = (apiClient as any).delete as jest.Mock;
const mockPatch = apiClient.patch as jest.Mock;

beforeEach(() => jest.clearAllMocks());

const apiLogResponse = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  date: '2024-01-15',
  user_id: '550e8400-e29b-41d4-a716-446655440099',
  entries: [{
    id: '550e8400-e29b-41d4-a716-446655440001',
    daily_log_id: '550e8400-e29b-41d4-a716-446655440000',
    product_id: '550e8400-e29b-41d4-a716-446655440002',
    product_name: 'Apple',
    amount_grams: 200,
    meal_type: 'breakfast',
    kcal_per_100g: 52,
    protein_per_100g: 0.3,
    fat_per_100g: 0.2,
    carbs_per_100g: 14,
    computed_kcal: 104,
    computed_protein: 0.6,
    computed_fat: 0.4,
    computed_carbs: 28,
  }],
  total_kcal: 104,
  total_protein: 0.6,
  total_fat: 0.4,
  total_carbs: 28,
};

describe('trackingService', () => {
  describe('logEntry', () => {
    it('posts entry and returns mapped log', async () => {
      mockPost.mockResolvedValue({ data: apiLogResponse });
      const result = await trackingService.logEntry({
        date: '2024-01-15',
        meal_type: 'breakfast' as any,
        product_id: '550e8400-e29b-41d4-a716-446655440002',
        amount_grams: 200,
      });
      expect(mockPost).toHaveBeenCalledWith('/api/v1/tracking/entries', expect.any(Object));
      expect(result.entries[0].calories).toBe(104);
      expect(result.entries[0].product.nutrition.calories_per_100g).toBe(52);
    });
  });

  describe('logEntriesBulk', () => {
    it('posts bulk entries', async () => {
      mockPost.mockResolvedValue({ data: apiLogResponse });
      const result = await trackingService.logEntriesBulk({
        date: '2024-01-15',
        meal_type: 'breakfast' as any,
        items: [{ product_id: 'id-1', amount_grams: 100 }],
      });
      expect(mockPost).toHaveBeenCalledWith('/api/v1/tracking/bulk-entries', expect.any(Object));
      expect(result.id).toBe(apiLogResponse.id);
    });
  });

  describe('getDailyLog', () => {
    it('fetches and maps daily log', async () => {
      mockGet.mockResolvedValue({ data: apiLogResponse });
      const result = await trackingService.getDailyLog('2024-01-15');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/tracking/daily/2024-01-15');
      expect(result.date).toBe('2024-01-15');
      expect(result.total_kcal).toBe(104);
      expect(result.entries[0].product.name).toBe('Apple');
    });
  });

  describe('deleteEntry', () => {
    it('calls delete endpoint', async () => {
      mockDelete.mockResolvedValue({});
      await trackingService.deleteEntry('entry-123');
      expect(mockDelete).toHaveBeenCalledWith('/api/v1/tracking/entries/entry-123');
    });
  });

  describe('updateEntry', () => {
    it('calls patch endpoint with updates', async () => {
      mockPatch.mockResolvedValue({});
      await trackingService.updateEntry('entry-123', { amount_grams: 300 });
      expect(mockPatch).toHaveBeenCalledWith('/api/v1/tracking/entries/entry-123', { amount_grams: 300 });
    });
  });

  describe('getHistory', () => {
    it('fetches history with date range', async () => {
      mockGet.mockResolvedValue({ data: [apiLogResponse] });
      const result = await trackingService.getHistory('2024-01-01', '2024-01-31');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/tracking/history', {
        params: { start_date: '2024-01-01', end_date: '2024-01-31' },
      });
      expect(result).toHaveLength(1);
      expect(result[0].date).toBe('2024-01-15');
    });
  });
});
