import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { trackingService } from "@/services/tracking.service";
import { DailyLog } from "@/types/food";

// Query keys factory for type safety and consistency
export const diaryKeys = {
  all: ["diary"] as const,
  byDate: (date: string) => ["diary", date] as const,
};

const DIARY_STALE_TIME = 1000 * 60 * 2; // 2 minutes

export function useDiary(date: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: diaryKeys.byDate(date),
    queryFn: () => trackingService.getDailyLog(date),
    staleTime: DIARY_STALE_TIME,
    gcTime: 1000 * 60 * 10, // 10 minutes cache
    refetchOnWindowFocus: false,
  });

  const deleteEntryMutation = useMutation({
    mutationFn: (entryId: string) => trackingService.deleteEntry(entryId),
    onMutate: async (entryId) => {
      await queryClient.cancelQueries({ queryKey: diaryKeys.byDate(date) });
      const previousLog = queryClient.getQueryData<DailyLog>(
        diaryKeys.byDate(date),
      );

      if (previousLog) {
        const deletedEntry = previousLog.entries.find((e) => e.id === entryId);
        const deletedCalories = deletedEntry?.calories ?? 0;
        const deletedProtein = deletedEntry?.protein ?? 0;
        const deletedFat = deletedEntry?.fat ?? 0;
        const deletedCarbs = deletedEntry?.carbs ?? 0;

        queryClient.setQueryData<DailyLog>(diaryKeys.byDate(date), {
          ...previousLog,
          entries: previousLog.entries.filter(
            (e: { id: string }) => e.id !== entryId,
          ),
          total_kcal: (previousLog.total_kcal ?? 0) - deletedCalories,
          total_protein: (previousLog.total_protein ?? 0) - deletedProtein,
          total_fat: (previousLog.total_fat ?? 0) - deletedFat,
          total_carbs: (previousLog.total_carbs ?? 0) - deletedCarbs,
        });
      }

      return { previousLog };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousLog) {
        queryClient.setQueryData(diaryKeys.byDate(date), context.previousLog);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: diaryKeys.byDate(date) });
    },
  });

  const updateEntryMutation = useMutation({
    mutationFn: ({
      id,
      ...data
    }: {
      id: string;
      amount_grams?: number;
      meal_type?: string;
    }) => trackingService.updateEntry(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: diaryKeys.byDate(date) });
    },
  });

  return {
    ...query,
    deleteEntry: deleteEntryMutation.mutate,
    updateEntry: updateEntryMutation.mutate,
  };
}
