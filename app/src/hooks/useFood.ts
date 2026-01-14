import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { foodService } from '@/services/food.service';
import { trackingService } from '@/services/tracking.service';
import { CreateEntryDto, CreateFoodDto } from '@/types/food';
import { useEffect, useState } from 'react';

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

  return useQuery({
    queryKey: ['foods', 'search', debouncedQuery],
    queryFn: () => foodService.searchFoods(debouncedQuery),
    enabled: debouncedQuery.length > 2, 
    staleTime: 1000 * 60 * 5, 
  });
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
