import { foodService, ensureFoodProduct } from '../../../services/food.service';
import { apiClient } from '../../../services/api.client';

jest.mock('../../../services/api.client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;

beforeEach(() => jest.clearAllMocks());

const apiFood = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'Apple',
  barcode: null,
  category: 'fruit',
  default_unit: null,
  nutrition: { kcal_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
  owner_id: null,
  source: 'fineli',
  brand: null,
  units: [],
};

describe('foodService', () => {
  describe('searchFoods', () => {
    it('maps kcal_per_100g to calories_per_100g', async () => {
      mockGet.mockResolvedValue({ data: [apiFood] });
      const results = await foodService.searchFoods('apple');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/foods/search', { params: { q: 'apple', external: false } });
      expect(results[0].nutrition.calories_per_100g).toBe(52);
      expect(results[0].name).toBe('Apple');
    });

    it('returns empty array for no results', async () => {
      mockGet.mockResolvedValue({ data: [] });
      const results = await foodService.searchFoods('nonexistent');
      expect(results).toEqual([]);
    });
  });

  describe('getFoodByBarcode', () => {
    it('fetches by barcode and maps response', async () => {
      mockGet.mockResolvedValue({ data: { ...apiFood, barcode: '123456' } });
      const result = await foodService.getFoodByBarcode('123456');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/foods/barcode/123456');
      expect(result.name).toBe('Apple');
    });
  });

  describe('createFood', () => {
    it('maps calories_per_100g to kcal_per_100g in payload', async () => {
      mockPost.mockResolvedValue({ data: apiFood });
      const result = await foodService.createFood({
        name: 'Custom Food',
        nutrition: { calories_per_100g: 100, protein_per_100g: 10, fat_per_100g: 5, carbs_per_100g: 15 },
      });
      expect(mockPost).toHaveBeenCalledWith('/api/v1/foods/custom', expect.objectContaining({
        nutrition: expect.objectContaining({ kcal_per_100g: 100 }),
      }));
      expect(result.nutrition.calories_per_100g).toBe(52);
    });
  });

  describe('getFoodById', () => {
    it('fetches food by ID', async () => {
      mockGet.mockResolvedValue({ data: apiFood });
      const result = await foodService.getFoodById('550e8400-e29b-41d4-a716-446655440000');
      expect(mockGet).toHaveBeenCalledWith('/api/v1/foods/550e8400-e29b-41d4-a716-446655440000');
      expect(result.id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });
  });
});

describe('ensureFoodProduct', () => {
  it('returns id from successfully created food', async () => {
    mockPost.mockResolvedValue({ data: apiFood });
    const id = await ensureFoodProduct({
      name: 'Apple',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    });
    expect(id).toBe('550e8400-e29b-41d4-a716-446655440000');
  });

  it('falls back to barcode lookup on conflict', async () => {
    mockPost.mockRejectedValue(new Error('Conflict'));
    mockGet.mockResolvedValue({ data: { ...apiFood, barcode: '123' } });
    const id = await ensureFoodProduct({
      name: 'Apple',
      barcode: '123',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    });
    expect(id).toBe('550e8400-e29b-41d4-a716-446655440000');
  });

  it('throws when no barcode to fall back to', async () => {
    mockPost.mockRejectedValue(new Error('Conflict'));
    await expect(ensureFoodProduct({
      name: 'Apple',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    })).rejects.toThrow();
  });

  it('throws when created food has null id', async () => {
    mockPost.mockResolvedValue({ data: { ...apiFood, id: null } });
    mockGet.mockRejectedValue(new Error('not found'));
    await expect(ensureFoodProduct({
      name: 'Apple',
      nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
    })).rejects.toThrow();
  });
});
