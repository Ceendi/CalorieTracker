import { useState, useMemo, useEffect } from 'react';
import { Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useLanguage } from '@/hooks/useLanguage';
import { useLogEntry, useUpdateEntry } from '@/hooks/useFood';
import { ensureFoodProduct } from '@/services/food.service';
import { FoodProduct, UnitInfo, MealType, CreateFoodDto, CreateEntryDto } from '@/types/food';
import { formatDateForApi } from '@/utils/date';

interface FoodEntryParams {
  entryId?: string;
  initialAmount?: string;
  initialMealType?: string;
  initialUnitLabel?: string;
  initialUnitGrams?: string;
  initialUnitQuantity?: string;
  date?: string;
}

export function useFoodEntry(food: FoodProduct | null, params: FoodEntryParams) {
  const router = useRouter();
  const { t } = useLanguage();
  
  const { 
    entryId, 
    initialAmount, 
    initialMealType, 
    initialUnitLabel, 
    initialUnitGrams, 
    initialUnitQuantity 
  } = params;

  // --- Initial State Logic ---
  const getInitialUnit = (): UnitInfo | null => {
    if (initialUnitLabel && initialUnitGrams) {
      return {
        label: initialUnitLabel,
        grams: parseFloat(initialUnitGrams),
        unit: initialUnitLabel
      };
    }
    return null;
  };

  const getInitialMealType = (): MealType => {
    if (initialMealType && Object.values(MealType).includes(initialMealType as MealType)) {
      return initialMealType as MealType;
    }
    const hour = new Date().getHours();
    if (hour < 10) return MealType.BREAKFAST;
    if (hour < 13) return MealType.LUNCH;
    if (hour < 17) return MealType.LUNCH;
    if (hour < 20) return MealType.DINNER;
    return MealType.SNACK;
  };

  // --- State ---
  const [selectedUnit, setSelectedUnit] = useState<UnitInfo | null>(getInitialUnit());
  const [quantity, setQuantity] = useState(
    initialUnitQuantity ? String(initialUnitQuantity) : (initialAmount ? String(initialAmount) : '100')
  );
  const [selectedMeal, setSelectedMeal] = useState<MealType>(getInitialMealType());

  // Reset state when food changes (but not when editing or when initialAmount provided)
  useEffect(() => {
    if (food && !entryId && !initialAmount) {
      setSelectedUnit(null);
      setQuantity('100');
    }
  }, [food, entryId, initialAmount]);

  // --- Derived Values ---
  const currentWeight = useMemo(() => {
    const qty = parseFloat(quantity) || 0;
    if (selectedUnit) {
      return qty * selectedUnit.grams;
    }
    return qty;
  }, [quantity, selectedUnit]);

  const ratio = currentWeight / 100;
  
  const macros = useMemo(() => {
    if (!food?.nutrition) {
      return { calories: 0, protein: 0, fat: 0, carbs: 0 };
    }
    return {
      calories: Math.round((food.nutrition.calories_per_100g || 0) * ratio),
      protein: (food.nutrition.protein_per_100g || 0) * ratio,
      fat: (food.nutrition.fat_per_100g || 0) * ratio,
      carbs: (food.nutrition.carbs_per_100g || 0) * ratio,
    };
  }, [food, ratio]);

  // --- Mutations ---
  const { mutate: logEntry, isPending: isLogging } = useLogEntry();
  const { mutate: updateEntry, isPending: isUpdating } = useUpdateEntry();
  const [isCreating, setIsCreating] = useState(false);

  const isBusy = isLogging || isCreating || isUpdating;

  const saveEntry = async () => {
    if (!food) return;

    try {
      if (entryId) {
        updateEntry({
          id: entryId,
          amount_grams: currentWeight,
          meal_type: selectedMeal,
          date: params.date as string
        }, {
          onSuccess: () => router.dismissAll(),
          onError: () => Alert.alert(t('foodDetails.errorTitle'), "Failed to update entry.")
        });
        return;
      }

      let productId = food.id;

      if (!productId) {
        setIsCreating(true);
        try {
          productId = await ensureFoodProduct({
            name: food.name,
            barcode: food.barcode,
            nutrition: food.nutrition
          });
        } finally {
          setIsCreating(false);
        }
      }

      if (!productId) {
        Alert.alert(t('foodDetails.errorTitle'), "Failed to resolve product ID");
        return;
      }

      const entry: CreateEntryDto = {
        date: formatDateForApi(),
        meal_type: selectedMeal,
        product_id: productId,
        amount_grams: currentWeight,
        unit_label: selectedUnit?.label,
        unit_grams: selectedUnit?.grams,
        unit_quantity: selectedUnit ? parseFloat(quantity) : undefined
      };

      logEntry(entry, {
        onSuccess: () => {
          router.dismissAll();
          router.replace('/(tabs)');
        },
        onError: (err) => {
          Alert.alert(t('foodDetails.errorTitle'), "Failed to add entry. Please try again.");
          console.error(err);
        }
      });

    } catch (e) {
      Alert.alert(t('foodDetails.errorTitle'), t('foodDetails.creationFailed'));
      console.error(e);
    }
  };

  return {
    quantity,
    setQuantity,
    selectedUnit,
    setSelectedUnit,
    selectedMeal,
    setSelectedMeal,
    macros,
    saveEntry,
    isBusy
  };
}
