import { renderHook, act, waitFor } from '@testing-library/react-native';
import { useMealPlans, useMealPlan, useDailyTargets, useDeleteMealPlan, useUpdatePlanStatus, useMealPlanGeneration, mealPlanKeys } from '@/hooks/useMealPlan';
import { createQueryWrapper } from '../helpers';

jest.mock('@/services/meal-plan.service', () => ({
  mealPlanService: {
    listPlans: jest.fn(),
    getPlan: jest.fn(),
    getDailyTargets: jest.fn(),
    deletePlan: jest.fn(),
    updatePlanStatus: jest.fn(),
    startGeneration: jest.fn(),
    getGenerationStatus: jest.fn(),
  },
}));

import { mealPlanService } from '@/services/meal-plan.service';

beforeEach(() => {
  jest.clearAllMocks();
});

describe('useMealPlans', () => {
  it('fetches meal plans list', async () => {
    (mealPlanService.listPlans as jest.Mock).mockResolvedValue({ plans: [{ id: 'p1', start_date: '2024-01-15', end_date: '2024-01-21', status: 'active' }] });
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useMealPlans(), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data?.plans).toHaveLength(1);
  });
});

describe('useMealPlan', () => {
  it('does not fetch when planId is null', () => {
    const { wrapper } = createQueryWrapper();
    renderHook(() => useMealPlan(null), { wrapper });
    expect(mealPlanService.getPlan).not.toHaveBeenCalled();
  });

  it('fetches plan when id provided', async () => {
    (mealPlanService.getPlan as jest.Mock).mockResolvedValue({
      id: 'plan-1',
      name: 'Test',
      start_date: '2024-01-15',
      end_date: '2024-01-21',
      status: 'active',
      days: [],
    });
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useMealPlan('plan-1'), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data?.id).toBe('plan-1');
  });
});

describe('useDailyTargets', () => {
  it('fetches daily targets', async () => {
    (mealPlanService.getDailyTargets as jest.Mock).mockResolvedValue({ kcal: 2000, protein: 150, fat: 70, carbs: 250 });
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useDailyTargets(), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data?.kcal).toBe(2000);
  });
});

describe('useDeleteMealPlan', () => {
  it('calls deletePlan service', async () => {
    (mealPlanService.deletePlan as jest.Mock).mockResolvedValue(undefined);
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useDeleteMealPlan(), { wrapper });

    act(() => {
      result.current.mutate('plan-1');
    });

    await waitFor(() => {
      expect(mealPlanService.deletePlan).toHaveBeenCalledWith('plan-1');
    });
  });
});

describe('useUpdatePlanStatus', () => {
  it('calls updatePlanStatus service', async () => {
    (mealPlanService.updatePlanStatus as jest.Mock).mockResolvedValue(undefined);
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useUpdatePlanStatus(), { wrapper });

    act(() => {
      result.current.mutate({ planId: 'plan-1', status: 'active' });
    });

    await waitFor(() => {
      expect(mealPlanService.updatePlanStatus).toHaveBeenCalledWith('plan-1', 'active');
    });
  });
});

describe('useMealPlanGeneration', () => {
  it('starts with idle state', () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useMealPlanGeneration(), { wrapper });

    expect(result.current.progress.status).toBe('idle');
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.isCompleted).toBe(false);
  });

  it('sets started status on generate', async () => {
    (mealPlanService.startGeneration as jest.Mock).mockResolvedValue({ task_id: 'task-1', message: 'Started' });
    (mealPlanService.getGenerationStatus as jest.Mock).mockResolvedValue({ status: 'generating', progress: 50 });

    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useMealPlanGeneration(), { wrapper });

    act(() => {
      result.current.generate({ start_date: '2024-01-15', days: 7 });
    });

    await waitFor(() => {
      expect(mealPlanService.startGeneration).toHaveBeenCalled();
    });
  });

  it('resets state', async () => {
    const { wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useMealPlanGeneration(), { wrapper });

    act(() => {
      result.current.reset();
    });

    expect(result.current.progress.status).toBe('idle');
    expect(result.current.progress.progress).toBe(0);
  });
});

describe('mealPlanKeys', () => {
  it('generates correct query keys', () => {
    expect(mealPlanKeys.all).toEqual(['meal-plans']);
    expect(mealPlanKeys.lists()).toEqual(['meal-plans', 'list']);
    expect(mealPlanKeys.list('active')).toEqual(['meal-plans', 'list', { status: 'active' }]);
    expect(mealPlanKeys.detail('id-1')).toEqual(['meal-plans', 'detail', 'id-1']);
    expect(mealPlanKeys.dailyTargets()).toEqual(['meal-plans', 'daily-targets']);
  });
});
