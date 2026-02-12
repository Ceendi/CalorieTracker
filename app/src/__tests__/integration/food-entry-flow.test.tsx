import { renderHook, act } from '@testing-library/react-native';
import { createQueryWrapper } from '../helpers';

// --- Service mocks ---
const mockSearchFoods = jest.fn();
const mockLogEntry = jest.fn();
const mockUpdateEntry = jest.fn();
const mockLogEntriesBulk = jest.fn();
const mockEnsureFoodProduct = jest.fn();

jest.mock('@/services/food.service', () => ({
  foodService: {
    searchFoods: (...args: any[]) => mockSearchFoods(...args),
    getByBarcode: jest.fn(),
    createFood: jest.fn(),
  },
  ensureFoodProduct: (...args: any[]) => mockEnsureFoodProduct(...args),
}));

jest.mock('@/services/tracking.service', () => ({
  trackingService: {
    logEntry: (...args: any[]) => mockLogEntry(...args),
    updateEntry: (...args: any[]) => mockUpdateEntry(...args),
    logEntriesBulk: (...args: any[]) => mockLogEntriesBulk(...args),
    getDailyLog: jest.fn(async () => ({ id: 'log-1', date: '2024-01-15', entries: [], total_kcal: 0, total_protein: 0, total_fat: 0, total_carbs: 0 })),
    deleteEntry: jest.fn(),
  },
}));

jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn(), dismissAll: jest.fn() })),
}));

jest.mock('@/hooks/useLanguage', () => ({
  useLanguage: () => ({ t: (k: string) => k, language: 'en', setLanguage: jest.fn() }),
}));

jest.mock('@/utils/date', () => ({
  formatDateForApi: jest.fn(() => '2024-01-15'),
}));

jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

import { useFoodEntry } from '@/hooks/useFoodEntry';
import { useLogEntry, useUpdateEntry } from '@/hooks/useFood';
import { FoodProduct, MealType } from '@/types/food';

// Mock the useFood hooks to return mutate functions
const mockLogEntryMutate = jest.fn();
const mockUpdateEntryMutate = jest.fn();

jest.mock('@/hooks/useFood', () => ({
  useLogEntry: () => ({ mutate: mockLogEntryMutate, isPending: false }),
  useUpdateEntry: () => ({ mutate: mockUpdateEntryMutate, isPending: false }),
  useFoodSearch: jest.fn(() => ({ data: undefined, isLoading: false })),
}));

const mockFood: FoodProduct = {
  id: 'food-1',
  name: 'Chicken Breast',
  nutrition: { calories_per_100g: 165, protein_per_100g: 31, fat_per_100g: 3.6, carbs_per_100g: 0 },
  units: [{ unit: 'piece', grams: 200, label: 'piece' }],
};

describe('Food Entry Flow Integration', () => {
  beforeEach(() => jest.clearAllMocks());

  it('creates new entry: select food → set quantity → save', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(mockFood, {}),
      { wrapper },
    );

    // Set quantity
    act(() => { result.current.setQuantity('200'); });
    expect(result.current.quantity).toBe('200');

    // Verify macros update
    expect(result.current.macros.calories).toBe(330); // 165 * 2

    // Save entry
    await act(async () => { await result.current.saveEntry(); });
    expect(mockLogEntryMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        product_id: 'food-1',
        amount_grams: 200,
      }),
      expect.any(Object),
    );
  });

  it('edits existing entry: load → modify → save', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(mockFood, {
        entryId: 'entry-1',
        initialAmount: '150',
        date: '2024-01-15',
      }),
      { wrapper },
    );

    expect(result.current.quantity).toBe('150');

    // Modify quantity
    act(() => { result.current.setQuantity('300'); });
    expect(result.current.macros.calories).toBe(495); // 165 * 3

    // Save edited entry
    await act(async () => { await result.current.saveEntry(); });
    expect(mockUpdateEntryMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'entry-1',
        amount_grams: 300,
      }),
      expect.any(Object),
    );
  });

  it('handles unit-based entry: select unit → set unit qty → correct grams', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(mockFood, {
        entryId: 'e1',
        initialUnitQuantity: '2',
        initialUnitLabel: 'piece',
        initialUnitGrams: '200',
      }),
      { wrapper },
    );

    expect(result.current.quantity).toBe('2');
    // 2 pieces × 200g = 400g → 165 * 4 = 660 kcal
    expect(result.current.macros.calories).toBe(660);
  });

  it('changes meal type before saving', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(mockFood, {}),
      { wrapper },
    );

    act(() => { result.current.setSelectedMeal(MealType.DINNER); });
    expect(result.current.selectedMeal).toBe(MealType.DINNER);

    await act(async () => { await result.current.saveEntry(); });
    expect(mockLogEntryMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        meal_type: MealType.DINNER,
      }),
      expect.any(Object),
    );
  });

  it('handles food without ID by calling ensureFoodProduct', async () => {
    const foodNoId: FoodProduct = { ...mockFood, id: null };
    mockEnsureFoodProduct.mockResolvedValue('new-product-id');

    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(foodNoId, {}),
      { wrapper },
    );

    await act(async () => { await result.current.saveEntry(); });
    expect(mockEnsureFoodProduct).toHaveBeenCalled();
    expect(mockLogEntryMutate).toHaveBeenCalledWith(
      expect.objectContaining({
        product_id: 'new-product-id',
      }),
      expect.any(Object),
    );
  });

  it('does nothing when saving with null food', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(
      () => useFoodEntry(null, {}),
      { wrapper },
    );

    await act(async () => { await result.current.saveEntry(); });
    expect(mockLogEntryMutate).not.toHaveBeenCalled();
    expect(mockUpdateEntryMutate).not.toHaveBeenCalled();
  });
});
