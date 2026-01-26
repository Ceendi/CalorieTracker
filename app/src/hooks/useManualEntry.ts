import { Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { format } from 'date-fns';
import { useForm, Control, SubmitHandler, UseFormSetValue, UseFormWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import { useLanguage } from '@/hooks/useLanguage';
import { useLogEntry, useCreateFood } from '@/hooks/useFood';
import { CreateFoodDto, CreateEntryDto, MealType } from '@/types/food';
import { manualFoodSchema, ManualFoodFormValues } from '@/schemas/food';

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
    resolver: zodResolver(manualFoodSchema) as any,
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
          const newFoodPayload: CreateFoodDto = {
              name: data.name,
              nutrition: {
                  calories_per_100g: data.calories,
                  protein_per_100g: data.protein,
                  fat_per_100g: data.fat,
                  carbs_per_100g: data.carbs
              }
          };
          
          let productId;
          try {
              const createdFood = await createFood(newFoodPayload);
              productId = createdFood.id;
          } catch (err) {
              console.error("Create manual food failed", err);
              Alert.alert(t('manualEntry.error'), t('manualEntry.createFailed'));
              return;
          }

          if (!productId) {
             Alert.alert(t('manualEntry.error'), "Failed to resolve product ID");
             return;
          }

          const entry: CreateEntryDto = {
              date: format(new Date(), 'yyyy-MM-dd'),
              meal_type: data.mealType, 
              product_id: productId,
              amount_grams: data.weight
          };

          logEntry(entry, {
              onSuccess: () => {
                  router.dismissAll();
                  router.replace('/(tabs)');
              },
              onError: (err) => {
                  Alert.alert(t('manualEntry.error'), "Failed to add entry. Please try again.");
                  console.error(err);
              }
          });

      } catch (e) {
          Alert.alert(t('manualEntry.error'), t('auth.unexpectedError'));
          console.error(e);
      }
  };

  return {
    control,
    submit: handleSubmit(onSubmit),
    setValue,
    watch,
    errors,
    isBusy
  };
}
