import { useState, useEffect, useMemo } from 'react';
import { Keyboard } from 'react-native';
import { ProcessedMeal, ProcessedFoodItem } from '@/services/ai.service';
import { FoodProduct } from '@/types/food';
import { summarizeMealMacros } from '@/utils/calculations';

interface UseVoiceMealLogicProps {
  initialMeal: ProcessedMeal | null;
  t: (key: string) => string;
}

export function useVoiceMealLogic({ initialMeal, t }: UseVoiceMealLogicProps) {
  const [localMeal, setLocalMeal] = useState<ProcessedMeal | null>(initialMeal);

  useEffect(() => {
    if (initialMeal) setLocalMeal(JSON.parse(JSON.stringify(initialMeal)));
  }, [initialMeal]);

  const totals = useMemo(() => {
    if (!localMeal?.items) return { kcal: 0, protein: 0, fat: 0, carbs: 0 };
    return summarizeMealMacros(localMeal.items);
  }, [localMeal]);

  const updateQuantity = (index: number, newValue: number, newUnit?: any) => {
    if (!localMeal) return;
    const updatedItems = [...localMeal.items];
    const item = { ...updatedItems[index] };

    const currentGrams = item.quantity_grams || 100;
    const kcalPerGram = item.kcal / currentGrams;
    const proteinPerGram = item.protein / currentGrams;
    const fatPerGram = item.fat / currentGrams;
    const carbsPerGram = item.carbs / currentGrams;

    const newGramsPerUnit = (newUnit === null || newUnit === undefined) ? 1 : newUnit.grams;
    item.unit_matched = (newUnit === null || newUnit === undefined) ? 'g' : newUnit.label;
    
    item.quantity_unit_value = newValue;
    item.quantity_grams = newValue * newGramsPerUnit;

    item.kcal = item.quantity_grams * kcalPerGram;
    item.protein = item.quantity_grams * proteinPerGram;
    item.fat = item.quantity_grams * fatPerGram;
    item.carbs = item.quantity_grams * carbsPerGram;
    
    updatedItems[index] = item;
    setLocalMeal({ ...localMeal, items: updatedItems });
  };

  const removeItem = (index: number) => {
    if (!localMeal) return;
    const updatedItems = localMeal.items.filter((_, i) => i !== index);
    setLocalMeal({ ...localMeal, items: updatedItems });
  };

  const cycleMealType = () => {
    if (!localMeal) return;
    const types = ['breakfast', 'second_breakfast', 'lunch', 'tea', 'dinner', 'snack'];
    const currentIdx = types.indexOf(localMeal.meal_type);
    const nextIdx = currentIdx === -1 ? 0 : (currentIdx + 1) % types.length;
    setLocalMeal({ ...localMeal, meal_type: types[nextIdx] });
  };

  const getMealTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      'breakfast': t('meals.breakfast'),
      'second_breakfast': t('meals.second_breakfast'),
      'lunch': t('meals.lunch'),
      'tea': t('meals.tea'),
      'dinner': t('meals.dinner'),
      'snack': t('meals.snack'),
      'śniadanie': t('meals.breakfast'),
      'drugie_śniadanie': t('meals.second_breakfast'),
      'obiad': t('meals.lunch'),
      'podwieczorek': t('meals.tea'),
      'kolacja': t('meals.dinner'),
      'przekąska': t('meals.snack'),
    };
    return labels[type] || type;
  };

  const addManualItem = (product: FoodProduct) => {
    if (!localMeal) return;
    const newItem: ProcessedFoodItem = {
      product_id: product.id ? parseInt(product.id) : null,
      name: product.name,
      quantity_grams: 100,
      quantity_unit_value: 100,
      unit_matched: 'g',
      kcal: product.nutrition.calories_per_100g,
      protein: product.nutrition.protein_per_100g,
      fat: product.nutrition.fat_per_100g,
      carbs: product.nutrition.carbs_per_100g,
      confidence: 1.0,
      status: 'matched',
      brand: product.brand,
      units: product.units,
    };

    setLocalMeal({
      ...localMeal,
      items: [...localMeal.items, newItem]
    });
    Keyboard.dismiss();
  };

  return {
    localMeal,
    totals,
    updateQuantity,
    removeItem,
    cycleMealType,
    getMealTypeLabel,
    addManualItem
  };
}
