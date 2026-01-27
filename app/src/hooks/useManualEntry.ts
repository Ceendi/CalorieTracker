import { Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useForm, Control, SubmitHandler, UseFormSetValue, UseFormWatch, Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { useLanguage } from '@/hooks/useLanguage';
import { useLogEntry, useCreateFood } from '@/hooks/useFood';
import { CreateFoodDto, CreateEntryDto, MealType } from '@/types/food';
import { manualFoodSchema, ManualFoodFormValues } from '@/schemas/food';
import { formatDateForApi } from '@/utils/date';

export type ManualEntryHookResult = {
  control: Control<ManualFoodFormValues>;
  submit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  setValue: UseFormSetValue<ManualFoodFormValues>;
  watch: UseFormWatch<ManualFoodFormValues>;
  isBusy: boolean;
};

export function useManualEntry() {
  const router = useRouter();
  const { t } = useLanguage();

  const getInitialMealType = (): MealType => {
      const hour = new Date().getHours();
      if (hour < 10) return MealType.BREAKFAST;
      if (hour < 13) return MealType.LUNCH;
      if (hour < 17) return MealType.SNACK;
      if (hour < 20) return MealType.DINNER;
      return MealType.SNACK;
  };

  const { control, handleSubmit, setValue, watch, formState: { errors } } = useForm<ManualFoodFormValues>({
    resolver: zodResolver(manualFoodSchema) as Resolver<ManualFoodFormValues>,
    defaultValues: {
      name: '',
      calories: 0,
      protein: 0,
      fat: 0,
      carbs: 0,
      weight: 100,
      mealType: getInitialMealType()
    }
  });

  const { mutate: logEntry, isPending: isLogging } = useLogEntry();
  const { mutateAsync: createFood, isPending: isCreating } = useCreateFood();

  const isBusy = isLogging || isCreating;

  const onSubmit: SubmitHandler<ManualFoodFormValues> = async (data) => {
      try {
          // Ensure numeric values are valid numbers
          const newFoodPayload: CreateFoodDto = {
              name: data.name.trim(),
              nutrition: {
                  calories_per_100g: Number(data.calories) || 0,
                  protein_per_100g: Number(data.protein) || 0,
                  fat_per_100g: Number(data.fat) || 0,
                  carbs_per_100g: Number(data.carbs) || 0
              }
          };

          let productId: string;
          try {
              const createdFood = await createFood(newFoodPayload);
              productId = createdFood.id!;
          } catch (err: any) {
              console.error("Create manual food failed", err);
              const errorMsg = err?.response?.data?.detail || t('manualEntry.createFailed');
              Alert.alert(t('manualEntry.error'), errorMsg);
              return;
          }

          if (!productId) {
             Alert.alert(t('manualEntry.error'), "Failed to resolve product ID");
             return;
          }

          const entry: CreateEntryDto = {
              date: formatDateForApi(),
              meal_type: data.mealType,
              product_id: productId,
              amount_grams: Number(data.weight) || 100
          };

          logEntry(entry, {
              onSuccess: () => {
                  router.dismissAll();
                  router.replace('/(tabs)');
              },
              onError: (err: any) => {
                  const errorMsg = err?.response?.data?.detail || "Failed to add entry. Please try again.";
                  Alert.alert(t('manualEntry.error'), errorMsg);
                  console.error(err);
              }
          });

      } catch (e: any) {
          const errorMsg = e?.response?.data?.detail || t('auth.unexpectedError');
          Alert.alert(t('manualEntry.error'), errorMsg);
          console.error(e);
      }
  };

  return {
    control: control as Control<ManualFoodFormValues>,
    submit: handleSubmit(onSubmit),
    setValue,
    watch,
    errors,
    isBusy
  };
}
