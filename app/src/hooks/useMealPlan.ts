import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback, useRef, useEffect } from 'react';
import { mealPlanService } from '@/services/meal-plan.service';
import {
  MealPlanListResponse,
  MealPlan,
  DailyTargets,
  GeneratePlanRequest,
  GenerationStatusResponse,
} from '@/schemas/meal-plan';

// Query keys factory for type safety and consistency
export const mealPlanKeys = {
  all: ['meal-plans'] as const,
  lists: () => [...mealPlanKeys.all, 'list'] as const,
  list: (status?: string) => [...mealPlanKeys.lists(), { status }] as const,
  details: () => [...mealPlanKeys.all, 'detail'] as const,
  detail: (id: string) => [...mealPlanKeys.details(), id] as const,
  dailyTargets: () => [...mealPlanKeys.all, 'daily-targets'] as const,
};

const MEAL_PLAN_STALE_TIME = 1000 * 60 * 5; // 5 minutes

/**
 * Hook to fetch list of meal plans.
 * @param status Optional filter by status
 */
export function useMealPlans(status?: string) {
  return useQuery({
    queryKey: mealPlanKeys.list(status),
    queryFn: () => mealPlanService.listPlans(status),
    staleTime: MEAL_PLAN_STALE_TIME,
    gcTime: 1000 * 60 * 15, // 15 minutes cache
  });
}

/**
 * Hook to fetch a single meal plan with all details.
 * @param planId UUID of the meal plan
 */
export function useMealPlan(planId: string | null) {
  return useQuery({
    queryKey: mealPlanKeys.detail(planId ?? ''),
    queryFn: () => mealPlanService.getPlan(planId!),
    enabled: !!planId,
    staleTime: MEAL_PLAN_STALE_TIME,
    gcTime: 1000 * 60 * 15,
  });
}

/**
 * Hook to fetch daily macro targets from backend.
 * Replaces local calculateDailyGoal calculation.
 */
export function useDailyTargets() {
  return useQuery({
    queryKey: mealPlanKeys.dailyTargets(),
    queryFn: () => mealPlanService.getDailyTargets(),
    staleTime: 1000 * 60 * 10, // 10 minutes - targets don't change often
    gcTime: 1000 * 60 * 30, // 30 minutes cache
    retry: 2,
  });
}

/**
 * Hook to delete a meal plan.
 */
export function useDeleteMealPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (planId: string) => mealPlanService.deletePlan(planId),
    onSuccess: () => {
      // Invalidate list queries to refetch
      queryClient.invalidateQueries({ queryKey: mealPlanKeys.lists() });
    },
  });
}

// Progress state for generation
export interface GenerationProgress {
  status: 'idle' | 'started' | 'generating' | 'completed' | 'error';
  progress: number;
  message?: string;
  planId?: string;
  error?: string;
  day?: number;
}

const POLLING_INTERVAL = 1000; // 1 second

/**
 * Hook for meal plan generation with polling-based progress tracking.
 * React Native doesn't have native EventSource, so we use polling instead.
 */
export function useMealPlanGeneration() {
  const queryClient = useQueryClient();
  const [generationProgress, setGenerationProgress] = useState<GenerationProgress>({
    status: 'idle',
    progress: 0,
  });
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const taskIdRef = useRef<string | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    taskIdRef.current = null;
  }, []);

  const pollStatus = useCallback(async (taskId: string) => {
    try {
      const status = await mealPlanService.getGenerationStatus(taskId);

      setGenerationProgress({
        status: status.status === 'unknown' ? 'error' : status.status,
        progress: status.progress ?? 0,
        message: status.message,
        planId: status.plan_id,
        error: status.error,
        day: status.day,
      });

      // Stop polling on completion or error
      if (status.status === 'completed' || status.status === 'error' || status.status === 'unknown') {
        stopPolling();

        // Invalidate list to show new plan
        if (status.status === 'completed') {
          queryClient.invalidateQueries({ queryKey: mealPlanKeys.lists() });
        }
      }
    } catch (error) {
      // Task not found - stop polling
      console.error('Polling error:', error);
      setGenerationProgress(prev => ({
        ...prev,
        status: 'error',
        error: 'Failed to get generation status',
      }));
      stopPolling();
    }
  }, [queryClient, stopPolling]);

  const startPolling = useCallback((taskId: string) => {
    taskIdRef.current = taskId;

    // Initial poll
    pollStatus(taskId);

    // Start interval polling
    pollingRef.current = setInterval(() => {
      if (taskIdRef.current) {
        pollStatus(taskIdRef.current);
      }
    }, POLLING_INTERVAL);
  }, [pollStatus]);

  const generateMutation = useMutation({
    mutationFn: (request: GeneratePlanRequest) => mealPlanService.startGeneration(request),
    onMutate: () => {
      setGenerationProgress({
        status: 'started',
        progress: 0,
        message: 'Starting generation...',
      });
    },
    onSuccess: (response) => {
      // Start polling for progress
      startPolling(response.task_id);
    },
    onError: (error: Error) => {
      setGenerationProgress({
        status: 'error',
        progress: 0,
        error: error.message,
      });
    },
  });

  const reset = useCallback(() => {
    stopPolling();
    setGenerationProgress({
      status: 'idle',
      progress: 0,
    });
  }, [stopPolling]);

  return {
    generate: generateMutation.mutate,
    generateAsync: generateMutation.mutateAsync,
    isStarting: generateMutation.isPending,
    progress: generationProgress,
    reset,
    isGenerating: generationProgress.status === 'started' || generationProgress.status === 'generating',
    isCompleted: generationProgress.status === 'completed',
    isError: generationProgress.status === 'error',
  };
}
