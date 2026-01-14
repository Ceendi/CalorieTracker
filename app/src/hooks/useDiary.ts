import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { trackingService } from '@/services/tracking.service';
import { CreateEntryDto, DailyLog } from '@/types/food';

export function useDiary(date: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['diary', date],
    queryFn: () => trackingService.getDailyLog(date),
  });

  const deleteEntryMutation = useMutation({
    mutationFn: (entryId: string) => trackingService.deleteEntry(entryId),
    onMutate: async (entryId) => {
      await queryClient.cancelQueries({ queryKey: ['diary', date] });
      const previousLog = queryClient.getQueryData<DailyLog>(['diary', date]);

      if (previousLog) {
        queryClient.setQueryData(['diary', date], {
          ...previousLog,
          entries: previousLog.entries.filter((e: { id: string }) => e.id !== entryId)
        });
      }

      return { previousLog };
    },
    onError: (err, variables, context) => {
      if (context?.previousLog) {
        queryClient.setQueryData(['diary', date], context.previousLog);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['diary', date] });
    },
  });

  const updateEntryMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: string, amount_grams?: number, meal_type?: string }) => 
      trackingService.updateEntry(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diary', date] });
    },
  });

  return {
    ...query,
    deleteEntry: deleteEntryMutation.mutate,
    updateEntry: updateEntryMutation.mutate,
  };
}
