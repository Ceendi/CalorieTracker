import { renderHook, act } from '@testing-library/react-native';
import { createQueryWrapper } from '../helpers';

// --- Mocks (must be before hook import) ---
const mockRouter = { push: jest.fn(), replace: jest.fn(), back: jest.fn(), dismissAll: jest.fn() };
jest.mock('expo-router', () => ({ useRouter: () => mockRouter }));
jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

const mockLogEntry = jest.fn();
const mockUpdateEntry = jest.fn();
jest.mock('@/hooks/useFood', () => ({
  useLogEntry: () => ({ mutate: mockLogEntry, isPending: false }),
  useUpdateEntry: () => ({ mutate: mockUpdateEntry, isPending: false }),
}));

jest.mock('@/services/food.service', () => ({
  ensureFoodProduct: jest.fn(),
}));
jest.mock('@/utils/date', () => ({
  formatDateForApi: jest.fn(() => '2024-01-15'),
}));

// Mock Alert
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

import { useFoodEntry } from '@/hooks/useFoodEntry';
import { FoodProduct, MealType } from '@/types/food';
import { ensureFoodProduct } from '@/services/food.service';

const mockFood: FoodProduct = {
  id: 'food-1',
  name: 'Apple',
  nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
};

describe('useFoodEntry', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('defaults quantity to 100', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      expect(result.current.quantity).toBe('100');
    });

    it('returns zero macros for null food', () => {
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(null, {}), { wrapper });
      expect(result.current.macros).toEqual({ calories: 0, protein: 0, fat: 0, carbs: 0 });
    });

    it('uses initialAmount when provided', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(
        () => useFoodEntry(food, { initialAmount: '250' }),
        { wrapper },
      );
      expect(result.current.quantity).toBe('250');
    });

    it('uses initialMealType when valid', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(
        () => useFoodEntry(food, { initialMealType: 'dinner' }),
        { wrapper },
      );
      expect(result.current.selectedMeal).toBe(MealType.DINNER);
    });

    it('sets initial unit from params', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      // entryId prevents useEffect from resetting selectedUnit
      const { result } = renderHook(
        () => useFoodEntry(food, { entryId: 'e1', initialUnitLabel: 'piece', initialUnitGrams: '120' }),
        { wrapper },
      );
      expect(result.current.selectedUnit).toEqual({ label: 'piece', grams: 120, unit: 'piece' });
    });

    it('uses initialUnitQuantity for quantity when provided', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      // entryId prevents useEffect from resetting quantity
      const { result } = renderHook(
        () => useFoodEntry(food, { entryId: 'e1', initialUnitQuantity: '3', initialUnitLabel: 'piece', initialUnitGrams: '50' }),
        { wrapper },
      );
      expect(result.current.quantity).toBe('3');
    });
  });

  describe('macros calculation', () => {
    it('calculates macros for 100g', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      expect(result.current.macros.calories).toBe(52);
      expect(result.current.macros.protein).toBeCloseTo(0.3);
      expect(result.current.macros.carbs).toBeCloseTo(14);
    });

    it('scales macros with quantity', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(
        () => useFoodEntry(food, { initialAmount: '200' }),
        { wrapper },
      );
      expect(result.current.macros.calories).toBe(104);
    });

    it('accounts for unit grams in macros', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      // entryId prevents useEffect from resetting selectedUnit
      const { result } = renderHook(
        () => useFoodEntry(food, { entryId: 'e1', initialUnitQuantity: '2', initialUnitLabel: 'piece', initialUnitGrams: '150' }),
        { wrapper },
      );
      // 2 * 150g = 300g → 52 * 3 = 156
      expect(result.current.macros.calories).toBe(156);
    });
  });

  describe('setQuantity', () => {
    it('updates quantity', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      act(() => { result.current.setQuantity('250'); });
      expect(result.current.quantity).toBe('250');
    });
  });

  describe('setSelectedMeal', () => {
    it('updates selected meal', () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      act(() => { result.current.setSelectedMeal(MealType.SNACK); });
      expect(result.current.selectedMeal).toBe(MealType.SNACK);
    });
  });

  describe('saveEntry', () => {
    it('does nothing when food is null', async () => {
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(null, {}), { wrapper });
      await act(async () => { await result.current.saveEntry(); });
      expect(mockLogEntry).not.toHaveBeenCalled();
      expect(mockUpdateEntry).not.toHaveBeenCalled();
    });

    it('calls logEntry for new entries with existing product id', async () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      await act(async () => { await result.current.saveEntry(); });
      expect(mockLogEntry).toHaveBeenCalledWith(
        expect.objectContaining({
          product_id: 'food-1',
          amount_grams: 100,
          date: '2024-01-15',
        }),
        expect.any(Object),
      );
    });

    it('calls updateEntry when entryId is provided', async () => {
      const food = { ...mockFood };
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(
        () => useFoodEntry(food, { entryId: 'entry-1', date: '2024-01-15' }),
        { wrapper },
      );
      await act(async () => { await result.current.saveEntry(); });
      expect(mockUpdateEntry).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'entry-1', amount_grams: 100 }),
        expect.any(Object),
      );
    });

    it('calls ensureFoodProduct when food has no id', async () => {
      const food: FoodProduct = { ...mockFood, id: null };
      (ensureFoodProduct as jest.Mock).mockResolvedValue('new-product-id');
      const { wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useFoodEntry(food, {}), { wrapper });
      await act(async () => { await result.current.saveEntry(); });
      expect(ensureFoodProduct).toHaveBeenCalled();
      expect(mockLogEntry).toHaveBeenCalledWith(
        expect.objectContaining({ product_id: 'new-product-id' }),
        expect.any(Object),
      );
    });
  });
});
