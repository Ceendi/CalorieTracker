import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { foodService } from '@/services/food.service';
import { trackingService } from '@/services/tracking.service';
import { CreateEntryDto, CreateFoodDto, CreateBulkEntryDto } from '@/types/food';
import { useEffect, useMemo, useState } from 'react';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function useFoodSearch(query: string) {
  const debouncedQuery = useDebounce(query, 300);
  const enabled = debouncedQuery.length > 2;

  // Stage 1: local DB only — fast, returns immediately
  const localQuery = useQuery({
    queryKey: ['foods', 'search', debouncedQuery, 'local'],
    queryFn: () => foodService.searchFoods(debouncedQuery, false),
    enabled,
    staleTime: 1000 * 60 * 5,
  });

  const localResults = localQuery.data;
  const fewLocalResults = !localQuery.isLoading && (localResults?.length ?? 0) < 5;

  // Stage 2: local + OFF — triggered only when local results are scarce
  const externalQuery = useQuery({
    queryKey: ['foods', 'search', debouncedQuery, 'external'],
    queryFn: () => foodService.searchFoods(debouncedQuery, true),
    enabled: enabled && fewLocalResults,
    staleTime: 1000 * 60 * 5,
  });

  // When external query finishes it already contains local+OFF merged by backend
  const data = useMemo(
    () => externalQuery.data ?? localResults,
    [externalQuery.data, localResults],
  );

  return {
    data,
    isLoading: localQuery.isLoading,
    isLoadingExternal: fewLocalResults && externalQuery.isLoading,
    isError: localQuery.isError,
    refetch: localQuery.refetch,
    isRefetching: localQuery.isRefetching,
  };
}

export function useFoodBarcode(barcode: string | null) {
  return useQuery({
    queryKey: ['foods', 'barcode', barcode],
    queryFn: () => foodService.getFoodByBarcode(barcode!),
    enabled: !!barcode,
    retry: false,
  });
}

export function useCreateFood() {
  return useMutation({
    mutationFn: (food: CreateFoodDto) => foodService.createFood(food),
  });
}

export function useLogEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entry: CreateEntryDto) => trackingService.logEntry(entry),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diary'] });
      queryClient.invalidateQueries({ queryKey: ['tracking', 'history'] });
    },
  });
}

export function useUpdateEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...data }: { id: string, amount_grams?: number, meal_type?: string, date?: string }) =>
      trackingService.updateEntry(id, data),
    onSuccess: (data, variables) => {
      if (variables.date) {
          queryClient.invalidateQueries({ queryKey: ['diary', variables.date] });
      } else {
          queryClient.invalidateQueries({ queryKey: ['diary'] });
      }
    },
  });
}

export function useLogEntriesBulk() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateBulkEntryDto) => trackingService.logEntriesBulk(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diary'] });
      queryClient.invalidateQueries({ queryKey: ['tracking', 'history'] });
    },
  });
}
