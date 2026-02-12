import { renderHook, act, waitFor } from '@testing-library/react-native';
import { useDiary, diaryKeys } from '@/hooks/useDiary';
import { createQueryWrapper } from '../helpers';

jest.mock('@/services/tracking.service', () => ({
  trackingService: {
    getDailyLog: jest.fn(),
    deleteEntry: jest.fn(),
    updateEntry: jest.fn(),
  },
}));

import { trackingService } from '@/services/tracking.service';

const mockLog = {
  id: 'log-1',
  date: '2024-01-15',
  entries: [
    {
      id: 'entry-1',
      product_id: 'prod-1',
      date: '2024-01-15',
      meal_type: 'breakfast' as const,
      amount_grams: 200,
      calories: 104,
      protein: 5,
      fat: 2,
      carbs: 20,
      product: {
        id: 'prod-1',
        name: 'Apple',
        nutrition: { calories_per_100g: 52, protein_per_100g: 0.3, fat_per_100g: 0.2, carbs_per_100g: 14 },
      },
    },
  ],
  total_kcal: 104,
  total_protein: 5,
  total_fat: 2,
  total_carbs: 20,
};

beforeEach(() => {
  jest.clearAllMocks();
  (trackingService.getDailyLog as jest.Mock).mockResolvedValue(mockLog);
});

describe('useDiary', () => {
  it('fetches daily log for given date', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useDiary('2024-01-15'), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(trackingService.getDailyLog).toHaveBeenCalledWith('2024-01-15');
    expect(result.current.data?.total_kcal).toBe(104);
  });

  it('uses correct query key', () => {
    expect(diaryKeys.byDate('2024-01-15')).toEqual(['diary', '2024-01-15']);
    expect(diaryKeys.all).toEqual(['diary']);
  });

  it('provides deleteEntry mutation', async () => {
    const { wrapper } = createQueryWrapper();
    (trackingService.deleteEntry as jest.Mock).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDiary('2024-01-15'), { wrapper });
    await waitFor(() => expect(result.current.data).toBeDefined());

    act(() => {
      result.current.deleteEntry('entry-1');
    });

    await waitFor(() => {
      expect(trackingService.deleteEntry).toHaveBeenCalledWith('entry-1');
    });
  });

  it('optimistically removes entry from cache on delete', async () => {
    const { wrapper, queryClient } = createQueryWrapper();
    // Make deleteEntry slow so we can observe the optimistic cache state
    let resolveDelete: () => void;
    (trackingService.deleteEntry as jest.Mock).mockImplementation(
      () => new Promise<void>((resolve) => { resolveDelete = resolve; })
    );

    const { result } = renderHook(() => useDiary('2024-01-15'), { wrapper });
    await waitFor(() => expect(result.current.data).toBeDefined());

    act(() => {
      result.current.deleteEntry('entry-1');
    });

    // While mutation is in-flight, cache should be optimistically updated
    await waitFor(() => {
      const cached = queryClient.getQueryData(diaryKeys.byDate('2024-01-15')) as any;
      expect(cached?.entries?.length).toBe(0);
    });

    // Resolve to prevent hanging
    act(() => { resolveDelete!(); });
  });

  it('provides updateEntry mutation', async () => {
    const { wrapper } = createQueryWrapper();
    (trackingService.updateEntry as jest.Mock).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDiary('2024-01-15'), { wrapper });
    await waitFor(() => expect(result.current.data).toBeDefined());

    act(() => {
      result.current.updateEntry({ id: 'entry-1', amount_grams: 300 });
    });

    await waitFor(() => {
      expect(trackingService.updateEntry).toHaveBeenCalledWith('entry-1', { amount_grams: 300 });
    });
  });
});
