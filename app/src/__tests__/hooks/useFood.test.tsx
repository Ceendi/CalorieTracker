import { renderHook, act, waitFor } from '@testing-library/react-native';
import { useFoodSearch, useFoodBarcode, useLogEntry, useLogEntriesBulk } from '@/hooks/useFood';
import { createQueryWrapper } from '../helpers';

jest.mock('@/services/food.service', () => ({
  foodService: {
    searchFoods: jest.fn(),
    getFoodByBarcode: jest.fn(),
    createFood: jest.fn(),
  },
}));

jest.mock('@/services/tracking.service', () => ({
  trackingService: {
    logEntry: jest.fn(),
    logEntriesBulk: jest.fn(),
    updateEntry: jest.fn(),
  },
}));

import { foodService } from '@/services/food.service';
import { trackingService } from '@/services/tracking.service';

const mockFoods = [
  { id: 'food-1', name: 'Apple', nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 } },
];

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('useFoodSearch', () => {
  it('does not search when query is too short', () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useFoodSearch('ab'), { wrapper });
    expect(result.current.data).toBeUndefined();
    expect(foodService.searchFoods).not.toHaveBeenCalled();
  });

  it('debounces search on value change', async () => {
    (foodService.searchFoods as jest.Mock).mockResolvedValue(mockFoods);
    const { wrapper } = createQueryWrapper();
    const { result, rerender } = renderHook(
      ({ q }: { q: string }) => useFoodSearch(q),
      { wrapper, initialProps: { q: 'app' } }
    );

    // Initial value fires immediately (useState initializes with value)
    await waitFor(() => {
      expect(foodService.searchFoods).toHaveBeenCalledWith('app');
    });

    (foodService.searchFoods as jest.Mock).mockClear();

    // Change query — should be debounced
    rerender({ q: 'apple' });

    // Immediately after rerender, debounced value hasn't changed yet
    expect(foodService.searchFoods).not.toHaveBeenCalled();

    // Advance past debounce delay
    act(() => {
      jest.advanceTimersByTime(350);
    });

    await waitFor(() => {
      expect(foodService.searchFoods).toHaveBeenCalledWith('apple');
    });
  });
});

describe('useFoodBarcode', () => {
  it('does not fetch when barcode is null', () => {
    const { wrapper } = createQueryWrapper();
    renderHook(() => useFoodBarcode(null), { wrapper });
    expect(foodService.getFoodByBarcode).not.toHaveBeenCalled();
  });

  it('fetches when barcode is provided', async () => {
    (foodService.getFoodByBarcode as jest.Mock).mockResolvedValue(mockFoods[0]);
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useFoodBarcode('123456'), { wrapper });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
    expect(foodService.getFoodByBarcode).toHaveBeenCalledWith('123456');
  });
});

describe('useLogEntry', () => {
  it('calls trackingService.logEntry', async () => {
    jest.useRealTimers();
    (trackingService.logEntry as jest.Mock).mockResolvedValue({ id: 'log-1' });
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useLogEntry(), { wrapper });

    act(() => {
      result.current.mutate({
        date: '2024-01-15',
        meal_type: 'breakfast' as any,
        product_id: 'food-1',
        amount_grams: 200,
      });
    });

    await waitFor(() => {
      expect(trackingService.logEntry).toHaveBeenCalled();
    });
  });
});

describe('useLogEntriesBulk', () => {
  it('calls trackingService.logEntriesBulk', async () => {
    jest.useRealTimers();
    (trackingService.logEntriesBulk as jest.Mock).mockResolvedValue({ id: 'log-1' });
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useLogEntriesBulk(), { wrapper });

    act(() => {
      result.current.mutate({
        date: '2024-01-15',
        meal_type: 'lunch' as any,
        items: [{ product_id: 'food-1', amount_grams: 100 }],
      });
    });

    await waitFor(() => {
      expect(trackingService.logEntriesBulk).toHaveBeenCalled();
    });
  });
});
